try:
    import argparse

    from levelkit_platform.engine.game import main
    from levelkit_platform.engine.errors import PlainEnglishError
except ModuleNotFoundError as exc:
    if exc.name == "pygame":
        raise SystemExit(
            "LevelKit Platform requires pygame, and pygame is not installed for this Python interpreter.\n"
            "Install it once for the Python you want to use, then run the game with that same Python:\n"
            "  python3 -m pip install -r requirements.txt\n"
            "  python3 run_game.py\n"
            "A virtual environment is optional; LevelKit does not require one."
        ) from exc
    raise


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description="Run LevelKit Platform.")
        parser.add_argument("--level", help="Start on this level id.")
        parser.add_argument("--spawn", default="default", help="Start at this spawn id.")
        args = parser.parse_args()
        main(starting_level=args.level, starting_spawn=args.spawn)
    except PlainEnglishError as exc:
        raise SystemExit(str(exc)) from exc
