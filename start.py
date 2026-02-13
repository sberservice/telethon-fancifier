import sys


def _venv_python_path(project_root):
    import os
    from pathlib import Path

    venv_dir = Path(project_root) / ".venv"
    return venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _install_deps(project_root):
    import subprocess

    install_target = ".[dev]" if "--dev" in sys.argv[2:] else "."
    use_system = "--system" in sys.argv[2:]

    if use_system:
        args = [sys.executable, "-m", "pip", "install", "-e", install_target]
        return subprocess.call(args, cwd=str(project_root))

    venv_python = _venv_python_path(project_root)

    if not venv_python.exists():
        from pathlib import Path

        venv_dir = Path(project_root) / ".venv"
        create_venv = [sys.executable, "-m", "venv", str(venv_dir)]
        create_code = subprocess.call(create_venv, cwd=str(project_root))
        if create_code != 0:
            return create_code

    args = [str(venv_python), "-m", "pip", "install", "-e", install_target]
    code = subprocess.call(args, cwd=str(project_root))
    if code == 0:
        sys.stdout.write(
            "Dependencies installed into .venv\n"
            "Use: .venv/bin/python start.py <command>\n"
        )
    return code


def _reexec_into_venv_if_available(project_root):
    import subprocess
    from pathlib import Path

    venv_python = _venv_python_path(project_root)
    if not venv_python.exists():
        return None

    current_python = Path(sys.executable).absolute()
    target_python = venv_python.absolute()
    if current_python == target_python:
        return None

    args = [str(venv_python), __file__, *sys.argv[1:]]
    return subprocess.call(args, cwd=str(project_root))


def main():
    if sys.version_info < (3, 12):
        sys.stderr.write(
            "telethon-fancifier requires Python 3.12+\n"
            "Run with: python3.12 start.py <command>\n"
        )
        raise SystemExit(1)

    from pathlib import Path

    project_root = Path(__file__).resolve().parent

    if len(sys.argv) >= 2 and sys.argv[1] == "install-deps":
        raise SystemExit(_install_deps(project_root))

    delegated_code = _reexec_into_venv_if_available(project_root)
    if delegated_code is not None:
        raise SystemExit(delegated_code)

    src_dir = project_root / "src"
    src_path = str(src_dir)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    try:
        from telethon_fancifier.cli import main as cli_main
    except ModuleNotFoundError as exc:
        if exc.name in {"dotenv", "telethon", "httpx", "platformdirs"}:
            sys.stderr.write(
                "Missing project dependencies in this Python environment.\n"
                "Install them with:\n"
                "  python3.12 start.py install-deps\n"
                "Then run from project venv:\n"
                "  .venv/bin/python start.py <command>\n"
            )
            raise SystemExit(1) from exc
        raise

    cli_main()


if __name__ == "__main__":
    main()