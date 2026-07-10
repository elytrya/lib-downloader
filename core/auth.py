import os

ENV_FILE = ".env"


def interactive_login() -> bool:
    print("\n" + "=" * 50)
    print("авторизация".center(50, "="))
    print("=" * 50)
    print("Для доступа к некоторым главам (18+ или скрытым) нужен токен вашего аккаунта.")
    print("\nКак получить токен:")
    print("  1. Откройте mangalib.me в вашем браузере")
    print("  2. Нажмите F12, чтобы открыть инструменты разработчика")
    print("  3. Перейдите во вкладку 'Console' (Консоль)")
    print("  4. Напишите в консоль `console.log(JSON.parse(localStorage.auth).token.access_token);`")
    print("  5. Скопируйте токен \n")

    token = input("Вставьте значение Authorization (или нажмите Enter для отмены): ").strip()
    if not token:
        print("Авторизация пропущена.")
        return False

    if not token.startswith("Bearer "):
        token = f"Bearer {token}"

    _save_to_env("MANGALIB_TOKEN", token)
    print("\nУспешно! Токен сохранен в файл .env!")
    print("=" * 50 + "\n")
    return True


def _save_to_env(key: str, value: str) -> None:
    env_data = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    env_data[k] = v
    env_data[key] = value
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        for k, v in env_data.items():
            f.write(f"{k}={v}\n")


def load_auth_cookies() -> dict:
    cookies = {}

    token = os.environ.get("MANGALIB_TOKEN")
    if token:
        cookies["mangalib_token"] = token

    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if "=" not in line:
                    continue
                k, v = line.strip().split("=", 1)
                if k == "MANGALIB_TOKEN":
                    cookies["mangalib_token"] = v
                elif k == "MANGALIB_SESSION":
                    cookies["mangalib_session"] = v
                elif k.startswith("MANGALIB_REMEMBER"):
                    cookies["remember_web"] = v
    return cookies
