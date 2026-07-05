content = open("karena/api/gateway.py", encoding="utf-8").read()

old = """def requires_permission(permission: Permission):
    async def dependency("""

new = """def requires_permission(permission: Permission):
    from karena.config import get_settings as _gs
    if not _gs().require_auth:
        async def _bypass() -> "TokenPayload":
            return TokenPayload(sub="dev", tenant_id="default", role="super_admin", permissions=list(Permission))
        return _bypass
    async def dependency("""

if old in content:
    content = content.replace(old, new)
    open("karena/api/gateway.py", "w", encoding="utf-8").write(content)
    print("Fixed!")
else:
    print("Pattern not found - checking...")
    idx = content.find("def requires_permission")
    print(content[idx:idx+200])
