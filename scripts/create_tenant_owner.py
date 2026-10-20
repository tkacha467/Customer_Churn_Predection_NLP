#!/usr/bin/env python3
"""
Secure Administrator & Tenant Owner Account Provisioning Tool.
Usage:
    python scripts/create_tenant_owner.py --email owner@example.com --tenant test_cafe_alpha --role owner --name "Cafe Owner"
"""

import argparse
import getpass
import os
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parents[1]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from api.review_assistant.auth import hash_password, get_store


def main():
    parser = argparse.ArgumentParser(description="Create or grant tenant access to an owner account.")
    parser.add_argument("--email", required=True, help="User email address")
    parser.add_argument("--tenant", required=True, help="Target business/tenant ID")
    parser.add_argument("--role", default="owner", choices=["owner", "manager", "staff"], help="Tenant role")
    parser.add_argument("--name", default="", help="Display name")
    parser.add_argument("--password", default="", help="Optional plaintext password (prompts if omitted)")
    parser.add_argument("--platform-admin", action="store_true", help="Grant platform administrator privileges")

    args = parser.parse_args()
    store = get_store()

    # Ensure target tenant exists
    if not store.tenant_exists(args.tenant):
        print(f"[-] Tenant '{args.tenant}' does not exist in the database.")
        create_it = input(f"Would you like to register '{args.tenant}' now? [y/N]: ").strip().lower()
        if create_it == "y":
            store.upsert_tenant({
                "id": args.tenant,
                "business_name": args.tenant.replace("_", " ").title()
            })
            print(f"[+] Tenant '{args.tenant}' created.")
        else:
            print("Aborted.")
            sys.exit(1)

    normalized_email = args.email.strip().lower()
    user = store.get_user_by_email(normalized_email)

    if not user:
        password = args.password
        if not password:
            password = getpass.getpass("Enter secure password (min 12 chars): ")
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                print("[-] Passwords do not match.")
                sys.exit(1)

        if len(password) < 12:
            print("[-] Password must contain at least 12 characters.")
            sys.exit(1)

        hashed = hash_password(password)
        user = store.create_user(
            email=normalized_email,
            password_hash=hashed,
            display_name=args.name or normalized_email.split("@")[0].title(),
            is_active=1,
            is_platform_admin=1 if args.platform_admin else 0
        )
        print(f"[+] User account '{normalized_email}' created (ID: {user['id']}).")
    else:
        print(f"[*] User account '{normalized_email}' found (ID: {user['id']}).")
        if args.platform_admin and not user.get("is_platform_admin"):
            with store._connect() as db:
                db.execute("UPDATE users SET is_platform_admin = 1 WHERE id = ?", (user["id"],))
            print(f"[+] User '{normalized_email}' promoted to Platform Administrator.")

    # Add or update membership
    membership = store.add_membership(user["id"], args.tenant, role=args.role)
    print(f"[+] User '{normalized_email}' granted '{args.role}' access to tenant '{args.tenant}'.")


if __name__ == "__main__":
    main()
