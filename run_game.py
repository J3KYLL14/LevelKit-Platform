try:
    from levelkit_platform.engine.game import main
    from levelkit_platform.engine.errors import PlainEnglishError
except ModuleNotFoundError as exc:
    if exc.name == "pygame":
        raise SystemExit(
            "LevelKit Platform requires pygame, and pygame is not installed for this Python interpreter.\n"
            "Use Python 3.13 (recommended) or another supported version with pygame available, then run:\n"
            "  python3 -m pip install -r requirements.txt\n"
            "  python3 run_game.py\n"
            "If you are using a virtual environment, make sure it was created with that same Python version."
        ) from exc
    raise


if __name__ == "__main__":
    try:
        main()
    except PlainEnglishError as exc:
        raise SystemExit(str(exc)) from exc
