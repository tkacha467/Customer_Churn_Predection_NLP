#!/usr/bin/env python3
"""
Secure Administrator & Tenant Owner Account Provisioning Tool.
Usage:
    python -m scripts.create_tenant_owner --email owner@example.com --tenant test_cafe_alpha --role owner --name "Cafe Owner"
"""

import argparse
import getpass
import os
import re
import sys
from pathlib import Path

root_dir = next((p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists() or (p / "Backend").exists()), Path(__file__).resolve().parents[2])
for _p in (root_dir, root_dir / "Backend"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from Backend.app.core.auth.auth import hash_password, get_store


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
TENANT_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]{2,64}$")


def validate_email_format(email: str) -> str:
    cleaned = email.strip().lower()
    if not EMAIL_REGEX.match(cleaned):
        raise ValueError(f"Invalid email address format: '{email}'")
    return cleaned


def validate_tenant_identifier(tenant_id: str) -> str:
    cleaned = tenant_id.strip().lower()
    if not TENANT_ID_REGEX.match(cleaned):
        raise ValueError(f"Invalid tenant ID '{tenant_id}'. Must be 2-64 alphanumeric characters, underscores, or dashes.")
    return cleaned


def resolve_password(args: argparse.Namespace) -> str:
    """
    Securely resolves password from stdin, environment variable, interactive prompt,
    or legacy CLI argument (with warning).
    """
    if args.password_stdin:
        pwd = sys.stdin.readline().rstrip("\r\n")
        if not pwd:
            raise ValueError("Empty password received from standard input (--password-stdin).")
        return pwd

    env_pwd = os.environ.get("OWNER_BOOTSTRAP_PASSWORD")
    if env_pwd:
        return env_pwd.strip()

    if args.password:
        sys.stderr.write(
            "[!] Security Warning: Supplying passwords via command-line arguments (--password) "
            "exposes credentials in process tables and shell history. "
            "Prefer interactive prompt, --password-stdin, or OWNER_BOOTSTRAP_PASSWORD.\n"
        )
        return args.password

    if sys.stdin.isatty():
        pwd = getpass.getpass("Enter secure password (min 12 chars): ")
        confirm = getpass.getpass("Confirm password: ")
        if pwd != confirm:
            raise ValueError("Passwords do not match.")
        return pwd

    raise ValueError(
        "No password provided in non-interactive environment. "
        "Use --password-stdin or OWNER_BOOTSTRAP_PASSWORD environment variable."
    )


def main():
    parser = argparse.ArgumentParser(
        description="Secure bootstrap tool for Vraja tenant owners and platform administrators."
    )
    parser.add_argument("--email", required=True, help="User email address")
    parser.add_argument("--tenant", required=True, help="Target business/tenant ID")
    parser.add_argument("--role", default="owner", choices=["owner", "manager", "staff"], help="Tenant role")
    parser.add_argument("--name", default="", help="Display name")
    parser.add_argument("--password", default="", help="Plaintext password flag (emits security warning)")
    parser.add_argument("--password-stdin", action="store_true", help="Read password safely from stdin without CLI exposure")
    parser.add_argument("--platform-admin", action="store_true", help="Explicitly grant platform administrator privileges")
    parser.add_argument("--auto-create-tenant", action="store_true", help="Automatically register tenant if it does not exist")

    args = parser.parse_args()

    try:
        normalized_email = validate_email_format(args.email)
        tenant_id = validate_tenant_identifier(args.tenant)
    except ValueError as e:
        print(f"[-] Validation Error: {e}", file=sys.stderr)
        sys.exit(1)

    store = get_store()

    # Ensure target tenant exists
    if not store.tenant_exists(tenant_id):
        print(f"[-] Tenant '{tenant_id}' does not exist in the database.")
        if args.auto_create_tenant or not sys.stdin.isatty():
            create_it = "y"
        else:
            create_it = input(f"Would you like to register '{tenant_id}' now? [y/N]: ").strip().lower()
        if create_it == "y":
            store.upsert_tenant({
                "id": tenant_id,
                "business_name": tenant_id.replace("_", " ").title()
            })
            print(f"[+] Tenant '{tenant_id}' created.")
        else:
            print("Aborted.")
            sys.exit(1)

    user = store.get_user_by_email(normalized_email)

    if not user:
        try:
            password = resolve_password(args)
        except ValueError as e:
            print(f"[-] Authentication Error: {e}", file=sys.stderr)
            sys.exit(1)

        if len(password) < 12:
            print("[-] Password policy error: Password must contain at least 12 characters.", file=sys.stderr)
            sys.exit(1)

        hashed = hash_password(password)
        # Clear plaintext reference
        del password

        user = store.create_user(
            email=normalized_email,
            password_hash=hashed,
            display_name=args.name or normalized_email.split("@")[0].title(),
            is_active=1,
            is_platform_admin=1 if args.platform_admin else 0
        )
        admin_tag = " (PLATFORM ADMIN)" if args.platform_admin else ""
        print(f"[+] User account '{normalized_email}' created{admin_tag} (ID: {user['id']}).")
    else:
        print(f"[*] User account '{normalized_email}' found (ID: {user['id']}).")
        if args.platform_admin and not user.get("is_platform_admin"):
            with store._connect() as db:
                db.execute("UPDATE users SET is_platform_admin = 1 WHERE id = ?", (user["id"],))
            print(f"[+] User '{normalized_email}' explicitly promoted to Platform Administrator.")

    # Add or update membership
    store.add_membership(user["id"], tenant_id, role=args.role)
    print(f"[+] User '{normalized_email}' granted '{args.role}' access to tenant '{tenant_id}'.")


if __name__ == "__main__":
    main()
