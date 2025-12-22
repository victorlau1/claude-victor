"""GitHub CLI wrapper for executing gh commands."""

import subprocess
import shutil
from typing import Optional


class GitHubClientError(Exception):
    """Exception raised for GitHub CLI errors."""

    def __init__(self, message: str, returncode: int = 1, stderr: str = ""):
        super().__init__(message)
        self.returncode = returncode
        self.stderr = stderr


class GitHubClient:
    """Wrapper around GitHub CLI (gh) for executing commands."""

    def __init__(self, repo: Optional[str] = None):
        """Initialize GitHub client.

        Args:
            repo: Optional repository in format 'owner/repo'. If not provided,
                  uses the current directory's git remote.
        """
        self.repo = repo
        self._verify_gh_installed()

    def _verify_gh_installed(self) -> None:
        """Verify that gh CLI is installed and accessible."""
        if not shutil.which("gh"):
            raise GitHubClientError(
                "GitHub CLI (gh) is not installed. Run 'make install' to install it."
            )

    def run_command(
        self,
        args: list[str],
        capture_output: bool = True,
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        """Execute a gh command with the given arguments.

        Args:
            args: Command arguments (without 'gh' prefix)
            capture_output: Whether to capture stdout/stderr
            check: Whether to raise exception on non-zero exit

        Returns:
            CompletedProcess with command results

        Raises:
            GitHubClientError: If command fails and check=True
        """
        cmd = ["gh"] + args

        if self.repo:
            cmd.extend(["--repo", self.repo])

        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                check=False,
            )

            if check and result.returncode != 0:
                raise GitHubClientError(
                    f"Command failed: {' '.join(cmd)}",
                    returncode=result.returncode,
                    stderr=result.stderr,
                )

            return result

        except FileNotFoundError:
            raise GitHubClientError("GitHub CLI (gh) not found in PATH")

    def check_auth(self) -> bool:
        """Check if user is authenticated with GitHub.

        Returns:
            True if authenticated, False otherwise
        """
        result = self.run_command(["auth", "status"], check=False)
        return result.returncode == 0

    def get_repo(self) -> Optional[str]:
        """Get the current repository name.

        Returns:
            Repository name in 'owner/repo' format, or None if not in a repo
        """
        if self.repo:
            return self.repo

        result = self.run_command(
            ["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
            check=False,
        )

        if result.returncode == 0:
            return result.stdout.strip()
        return None

    def api(
        self,
        endpoint: str,
        method: str = "GET",
        fields: Optional[dict] = None,
    ) -> str:
        """Make a GitHub API request.

        Args:
            endpoint: API endpoint (e.g., '/repos/{owner}/{repo}/issues')
            method: HTTP method (GET, POST, PATCH, DELETE)
            fields: Optional fields to include in request body

        Returns:
            API response as string
        """
        args = ["api", endpoint, "-X", method]

        if fields:
            for key, value in fields.items():
                args.extend(["-f", f"{key}={value}"])

        result = self.run_command(args)
        return result.stdout
