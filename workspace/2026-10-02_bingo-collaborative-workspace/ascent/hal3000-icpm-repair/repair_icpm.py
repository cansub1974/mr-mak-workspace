"""Give one BCW account the ICPM (administrator) role again, when no account has it.

Preview (changes nothing):   python -I -B repair_icpm.py --account bmt01
Repair:                      python -I -B repair_icpm.py --account bmt01 --execute

The repair first copies BCW's database to data\\backups\\icpm-repair-<time>\\ and checks the copy.
It then adds ICPM to the account's roles (keeping its other roles), to its active deployment
(so a later deployment edit does not strip it again), sets the account's old-style role to admin,
and records the change in BCW's audit history. BCW can keep running: it re-reads roles on every click.
"""
import argparse, json, sqlite3, sys
from datetime import datetime, timezone
from pathlib import Path

ICPM = 'ICPM'


def say(text=''):
    print(text, flush=True)


def data_folder(explicit):
    if explicit:
        return Path(explicit)
    marker = Path(r'C:\BCW\installation.json')
    if marker.is_file():
        value = json.loads(marker.read_text('utf-8-sig'))
        if value.get('data_root'):
            return Path(value['data_root'])
    import os
    return Path(os.environ.get('USERPROFILE', str(Path.home()))) / 'Documents' / 'BCW' / 'data'


def accounts(c):
    return c.execute(
        "SELECT u.id, u.name, u.role, s.role_positions, s.occupant, s.version, "
        "a.enabled, a.archived, a.blocked FROM users u JOIN staff_accounts s ON s.user_id=u.id "
        "LEFT JOIN account_state a ON a.user_id=u.id ORDER BY u.name").fetchall()


def usable(row):
    return (row['enabled'] is None or row['enabled']) and not row['archived'] and not row['blocked']


def show(c):
    say('Accounts now:')
    for r in accounts(c):
        state = 'enabled' if usable(r) else 'NOT USABLE (disabled, archived or pending)'
        say(f"  {r['name']:<8} roles {', '.join(json.loads(r['role_positions'] or '[]')) or '(none)':<34} "
            f"occupant {r['occupant'] or '-':<18} {state}")
    holders = [r['name'] for r in accounts(c) if ICPM in json.loads(r['role_positions'] or '[]') and usable(r)]
    say('Accounts with ICPM: ' + (', '.join(holders) if holders else 'NONE'))
    say()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--account', required=True)
    p.add_argument('--data')
    p.add_argument('--execute', action='store_true')
    a = p.parse_args()

    data = data_folder(a.data)
    db = data / 'context.sqlite'
    if not db.is_file():
        say(f'BCW database not found at {db}.')
        say('Sign in to Windows as the user that runs BCW, then run this again.')
        return 2
    say(f'BCW data folder: {data}')

    c = sqlite3.connect(db, timeout=30)
    c.row_factory = sqlite3.Row
    show(c)

    target = next((r for r in accounts(c) if a.account.lower() in (r['id'].lower(), r['name'].lower())), None)
    if not target:
        say(f'No laptop account called {a.account}. Nothing changed.')
        return 2
    if not usable(target):
        say(f"{target['name']} is disabled, archived or waiting for an administration operation.")
        say('This repair does not change that. Nothing changed.')
        return 2
    roles = json.loads(target['role_positions'] or '[]')
    deployment = c.execute("SELECT id, role_positions FROM deployments WHERE account_id=? AND status='Active'",
                           (target['id'],)).fetchone()
    dep_roles = json.loads(deployment['role_positions']) if deployment else None

    need_account = ICPM not in roles or target['role'] != 'admin'
    need_deployment = deployment is not None and ICPM not in dep_roles
    if not need_account and not need_deployment:
        say(f"{target['name']} already has ICPM. Nothing to do: reload BCW in the browser (F5) and sign in as {target['name']}.")
        return 0

    new_roles = [ICPM] + [r for r in roles if r != ICPM]
    say(f"Planned change for {target['name']} (occupant {target['occupant'] or '-'}):")
    say(f"  account roles:    {', '.join(roles) or '(none)'}  ->  {', '.join(new_roles)}")
    if deployment:
        new_dep = [ICPM] + [r for r in dep_roles if r != ICPM]
        say(f"  active deployment roles: {', '.join(dep_roles) or '(none)'}  ->  {', '.join(new_dep)}")
    else:
        say('  (no active deployment on this account)')
    say()
    if not a.execute:
        say('PREVIEW ONLY. Nothing has been changed.')
        return 0

    stamp = datetime.now(timezone.utc)
    folder = data / 'backups' / ('icpm-repair-' + stamp.strftime('%Y%m%d-%H%M%S'))
    folder.mkdir(parents=True, exist_ok=False)
    copy = sqlite3.connect(folder / 'context.sqlite')
    c.backup(copy)
    ok = copy.execute('PRAGMA integrity_check').fetchone()[0]
    copy.close()
    if ok != 'ok':
        say(f'The backup copy failed its check ({ok}). Nothing changed.')
        return 1
    say(f'Backup taken and checked: {folder}')

    try:
        c.execute('BEGIN IMMEDIATE')
        current = c.execute('SELECT role_positions, version FROM staff_accounts WHERE user_id=?', (target['id'],)).fetchone()
        if current['version'] != target['version']:
            raise RuntimeError('the account changed while this ran; run the repair again')
        c.execute('UPDATE staff_accounts SET role_positions=?, version=version+1 WHERE user_id=?',
                  (json.dumps(new_roles), target['id']))
        c.execute('UPDATE account_state SET version=version+1 WHERE user_id=?', (target['id'],))
        c.execute("UPDATE users SET role='admin' WHERE id=?", (target['id'],))
        if need_deployment:
            c.execute('UPDATE deployments SET role_positions=?, version=version+1 WHERE id=?',
                      (json.dumps(new_dep), deployment['id']))
        c.execute('INSERT INTO events(actor,action,target,data,created) VALUES(?,?,?,?,?)',
                  ('maintenance', 'account.assignments', target['id'],
                   json.dumps({'repair': 'icpm-restored', 'before': {'role_positions': roles},
                               'after': {'role_positions': new_roles}, 'backup': str(folder),
                               'actor_occupant': 'BCW maintenance (ICPM repair)'}),
                   stamp.isoformat()))
        c.commit()
    except Exception as error:
        c.rollback()
        say(f'Repair stopped and was undone: {error}')
        return 1

    say()
    show(c)
    after = c.execute('SELECT role_positions FROM staff_accounts WHERE user_id=?', (target['id'],)).fetchone()
    if ICPM in json.loads(after[0]):
        say(f"DONE. {target['name']} is ICPM again.")
        say(f"In the browser press F5 (or sign out and in) as {target['name']}: Tools > Admin is back.")
        return 0
    say('The change did not read back as expected. Keep this window and report it.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
