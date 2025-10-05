"""Main CLI entry point for Capibara Core."""

import asyncio
import os

import click
from rich.console import Console
from rich.table import Table

from capibara.sdk.client import CapibaraClient
from capibara.utils.logging import get_logger

logger = get_logger(__name__)
console = Console()


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--config", "-c", help="Path to configuration file")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, config: str | None) -> None:
    """Capibara - Generate executable scripts from natural language prompts."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config"] = config

    if verbose:
        console.print("Verbose logging enabled", style="dim")


@cli.command()
@click.argument("prompt")
@click.option("--language", "-l", default="python", help="Programming language")
@click.option("--execute", "-e", is_flag=True, help="Execute the generated script")
@click.option("--security-policy", "-s", help="Security policy to apply")
@click.option("--provider", "-p", help="LLM provider to use")
@click.option("--context", help="Additional context as JSON")
@click.pass_context
def run(
    ctx: click.Context,
    prompt: str,
    language: str,
    execute: bool,
    security_policy: str | None,
    provider: str | None,
    context: str | None,
) -> None:
    """Generate and optionally execute a script from a natural language prompt."""
    asyncio.run(
        _run_script(ctx, prompt, language, execute, security_policy, provider, context)
    )


@cli.command()
@click.option("--limit", "-n", default=50, help="Maximum number of scripts to show")
@click.option("--offset", "-o", default=0, help="Number of scripts to skip")
@click.option("--language", "-l", help="Filter by programming language")
@click.option("--search", "-s", help="Search in prompts and code")
@click.option("--sort-by", default="created_at", help="Sort field")
@click.option("--sort-order", default="desc", help="Sort order (asc/desc)")
@click.pass_context
def list_scripts(
    ctx: click.Context,
    limit: int,
    offset: int,
    language: str | None,
    search: str | None,
    sort_by: str,
    sort_order: str,
) -> None:
    """List cached scripts."""
    asyncio.run(
        _list_scripts(ctx, limit, offset, language, search, sort_by, sort_order)
    )


@cli.command()
@click.argument("script_id")
@click.option("--code/--no-code", default=True, help="Include generated code")
@click.option("--logs/--no-logs", default=False, help="Include execution logs")
@click.pass_context
def show(ctx: click.Context, script_id: str, code: bool, logs: bool) -> None:
    """Show details of a specific script."""
    asyncio.run(_show_script(ctx, script_id, code, logs))


@cli.command()
@click.option("--script-ids", help="Comma-separated list of script IDs to clear")
@click.option("--language", "-l", help="Clear all scripts of specific language")
@click.option("--older-than", help="Clear scripts older than N seconds")
@click.option("--all", is_flag=True, help="Clear all cached scripts")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def clear(
    ctx: click.Context,
    script_ids: str | None,
    language: str | None,
    older_than: int | None,
    all: bool,
    confirm: bool,
) -> None:
    """Clear cache or specific scripts."""
    asyncio.run(_clear_cache(ctx, script_ids, language, older_than, all, confirm))


@cli.command()
@click.option(
    "--quick",
    "-q",
    is_flag=True,
    help="Run quick health check (critical components only)",
)
@click.option("--json", is_flag=True, help="Output results in JSON format")
@click.pass_context
def health(ctx: click.Context, quick: bool, json: bool) -> None:
    """Check health of all components."""
    asyncio.run(_health_check(ctx, quick, json))


@cli.command()
@click.pass_context
def stats(ctx: click.Context) -> None:
    """Show statistics for all components."""
    asyncio.run(_show_stats(ctx))


@cli.command()
@click.pass_context
def doctor(ctx: click.Context) -> None:
    """Check system health and dependencies."""
    asyncio.run(_doctor_check(ctx))


async def _run_script(
    ctx: click.Context,
    prompt: str,
    language: str,
    execute: bool,
    security_policy: str | None,
    provider: str | None,
    context: str | None,
) -> None:
    """Run script generation."""
    try:
        # Parse context if provided
        context_dict = None
        if context:
            import json

            context_dict = json.loads(context)

        # Initialize client
        client = _get_client(ctx)

        # Generate script
        console.print(f"[bold blue]Generating {language} script...[/bold blue]")
        console.print(f"[dim]Prompt: {prompt}[/dim]")

        response = await client.run(
            prompt=prompt,
            language=language,
            context=context_dict,
            security_policy=security_policy,
            llm_provider=provider,
            execute=execute,
        )

        # Display results
        console.print("\n[bold green]Script generated successfully![/bold green]")
        console.print(f"[dim]Script ID: {response.script_id}[/dim]")
        console.print(f"[dim]Provider: {response.llm_provider}[/dim]")
        console.print(f"[dim]Cached: {response.cached}[/dim]")

        if response.cached:
            console.print(f"[dim]Cache hits: {response.cache_hit_count}[/dim]")

        # Show generated code
        console.print("\n[bold]Generated Code:[/bold]")
        console.print(f"[code]{response.code}[/code]")

        # Show execution result if executed
        if execute and response.execution_result:
            result = response.execution_result
            console.print("\n[bold]Execution Result:[/bold]")
            console.print(f"Success: {result.success}")
            console.print(f"Exit Code: {result.exit_code}")
            console.print(f"Execution Time: {result.execution_time_ms}ms")
            console.print(f"Memory Used: {result.memory_used_mb:.1f}MB")

            if result.stdout:
                console.print("\n[bold]Output:[/bold]")
                console.print(f"[code]{result.stdout}[/code]")

            if result.stderr:
                console.print("\n[bold]Error Output:[/bold]")
                console.print(f"[red]{result.stderr}[/red]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if ctx.obj.get("verbose"):
            console.print_exception()


async def _list_scripts(
    ctx: click.Context,
    limit: int,
    offset: int,
    language: str | None,
    search: str | None,
    sort_by: str,
    sort_order: str,
) -> None:
    """List cached scripts."""
    try:
        client = _get_client(ctx)

        response = await client.list_scripts(
            limit=limit,
            offset=offset,
            language=language,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        if not response.scripts:
            console.print("[yellow]No scripts found[/yellow]")
            return

        # Create table
        table = Table(title="Cached Scripts")
        table.add_column("Script ID", style="cyan")
        table.add_column("Language", style="green")
        table.add_column("Prompt", style="white", max_width=50)
        table.add_column("Created", style="dim")
        table.add_column("Executions", style="blue")
        table.add_column("Cache Hits", style="magenta")

        for script in response.scripts:
            table.add_row(
                script.script_id[:12] + "...",
                script.language,
                (
                    script.prompt[:47] + "..."
                    if len(script.prompt) > 50
                    else script.prompt
                ),
                script.created_at.strftime("%Y-%m-%d %H:%M"),
                str(script.execution_count),
                str(script.cache_hit_count),
            )

        console.print(table)
        console.print(
            f"\n[dim]Showing {len(response.scripts)} of {response.total_count} scripts[/dim]"
        )

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if ctx.obj.get("verbose"):
            console.print_exception()


async def _show_script(
    ctx: click.Context, script_id: str, code: bool, logs: bool
) -> None:
    """Show script details."""
    try:
        client = _get_client(ctx)

        response = await client.show_script(
            script_id=script_id,
            include_code=code,
            include_execution_logs=logs,
        )

        script = response.script

        # Display script info
        console.print("[bold]Script Details[/bold]")
        console.print(f"ID: {script.script_id}")
        console.print(f"Language: {script.language}")
        console.print(f"Provider: {script.llm_provider}")
        console.print(f"Created: {script.created_at}")
        console.print(f"Updated: {script.updated_at}")
        console.print(f"Executions: {script.execution_count}")
        console.print(f"Cache Hits: {script.cache_hit_count}")
        console.print(f"Size: {script.size_bytes} bytes")

        if script.security_policy:
            console.print(f"Security Policy: {script.security_policy}")

        console.print("\n[bold]Prompt:[/bold]")
        console.print(f"[dim]{script.prompt}[/dim]")

        if code and response.code:
            console.print("\n[bold]Generated Code:[/bold]")
            console.print(f"[code]{response.code}[/code]")

        if logs and response.execution_logs:
            console.print("\n[bold]Execution Logs:[/bold]")
            for log in response.execution_logs:
                console.print(f"[dim]{log}[/dim]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if ctx.obj.get("verbose"):
            console.print_exception()


async def _clear_cache(
    ctx: click.Context,
    script_ids: str | None,
    language: str | None,
    older_than: int | None,
    all: bool,
    confirm: bool,
) -> None:
    """Clear cache."""
    try:
        client = _get_client(ctx)

        # Parse script IDs
        script_id_list = None
        if script_ids:
            script_id_list = [id.strip() for id in script_ids.split(",")]

        # Confirm if not already confirmed
        if not confirm and (all or script_id_list):
            if all:
                confirm_text = "Are you sure you want to clear ALL cached scripts?"
            else:
                confirm_text = f"Are you sure you want to clear {len(script_id_list) if script_id_list else 0} scripts?"

            if not click.confirm(confirm_text):
                console.print("Operation cancelled")
                return

        # Clear cache
        response = await client.clear_cache(
            script_ids=script_id_list,
            language=language,
            older_than=older_than,
            all_scripts=all,
        )

        console.print(
            f"[bold green]Cleared {response.cleared_count} scripts[/bold green]"
        )
        if response.total_size_freed_bytes > 0:
            console.print(f"[dim]Freed {response.total_size_freed_bytes} bytes[/dim]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if ctx.obj.get("verbose"):
            console.print_exception()


async def _health_check(
    ctx: click.Context, quick: bool = False, json_output: bool = False
) -> None:
    """Check health of all components."""
    try:
        client = _get_client(ctx)

        health = await client.health_check()

        if json_output:
            import json

            console.print(json.dumps(health, indent=2, default=str))
            return

        console.print("[bold]Health Check[/bold]")
        console.print(
            f"Overall: {'[green]Healthy[/green]' if health['overall'] else '[red]Unhealthy[/red]'}"
        )

        if quick:
            # Show only critical components
            critical_components = ["cache", "llm_providers", "container_runner"]
            for component in critical_components:
                if component in health["components"]:
                    status = health["components"][component]
                    if status["healthy"]:
                        console.print(f"{component}: [green]Healthy[/green]")
                    else:
                        console.print(f"{component}: [red]Unhealthy[/red]")
                        if "error" in status:
                            console.print(f"  Error: {status['error']}")
        else:
            # Show all components
            for component, status in health["components"].items():
                if status["healthy"]:
                    console.print(f"{component}: [green]Healthy[/green]")
                else:
                    console.print(f"{component}: [red]Unhealthy[/red]")
                    if "error" in status:
                        console.print(f"  Error: {status['error']}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if ctx.obj.get("verbose"):
            console.print_exception()


async def _show_stats(ctx: click.Context) -> None:
    """Show statistics."""
    try:
        client = _get_client(ctx)

        stats = client.get_stats()

        console.print("[bold]Statistics[/bold]")

        # Cache stats
        cache_stats = stats["cache"]
        console.print("\n[bold]Cache[/bold]")
        console.print(f"Hits: {cache_stats['hits']}")
        console.print(f"Misses: {cache_stats['misses']}")
        console.print(f"Hit Rate: {cache_stats['hit_rate_percent']:.1f}%")
        console.print(f"Total Scripts: {cache_stats['total_scripts']}")
        console.print(f"Total Size: {cache_stats['total_size_bytes']} bytes")

        # LLM Provider stats
        provider_stats = stats["llm_providers"]
        console.print("\n[bold]LLM Providers[/bold]")
        console.print(f"Total Requests: {provider_stats['total_requests']}")
        console.print(f"Success Rate: {provider_stats['success_rate']:.1f}%")

        for provider, stats in provider_stats["providers"].items():
            console.print(
                f"  {provider}: {stats['successes']}/{stats['requests']} ({stats['success_rate']:.1f}%)"
            )

        # Script Generator stats
        gen_stats = stats["script_generator"]
        console.print("\n[bold]Script Generation[/bold]")
        console.print(f"Total Generations: {gen_stats['total_generations']}")
        console.print(f"Success Rate: {gen_stats['success_rate_percent']:.1f}%")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if ctx.obj.get("verbose"):
            console.print_exception()


async def _doctor_check(ctx: click.Context) -> None:
    """Check system health and dependencies."""
    import sys

    import docker
    from rich.panel import Panel

    # Create health check table
    table = Table(title="Capibara Core Health Check")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="white")

    # Check Python version
    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    table.add_row(
        "Python",
        "✅ OK" if sys.version_info >= (3, 11) else "❌ FAIL",
        (
            f"v{python_version}"
            if sys.version_info >= (3, 11)
            else f"v{python_version} (requires 3.11+)"
        ),
    )

    # Check Docker
    try:
        docker_client = docker.from_env()
        docker_client.ping()
        docker_version = docker_client.version()["Version"]
        table.add_row("Docker", "✅ OK", f"v{docker_version}")
    except Exception as e:
        table.add_row("Docker", "❌ FAIL", f"Not running or not installed: {str(e)}")

    # Check API keys
    groq_key = os.getenv("GROQ_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if groq_key:
        table.add_row("Groq API", "✅ OK", "Key configured")
    else:
        table.add_row("Groq API", "⚠️  WARN", "No key found (set GROQ_API_KEY)")

    if openai_key:
        table.add_row("OpenAI API", "✅ OK", "Key configured")
    else:
        table.add_row("OpenAI API", "⚠️  WARN", "No key found (set OPENAI_API_KEY)")

    # Check cache directory
    cache_dir = os.path.expanduser("~/.capibara/cache")
    if os.path.exists(cache_dir):
        table.add_row("Cache", "✅ OK", f"Directory exists: {cache_dir}")
    else:
        table.add_row("Cache", "ℹ️  INFO", "Will be created on first use")

    console.print(table)

    # Overall status
    if "❌ FAIL" in str(table):
        console.print(
            Panel("❌ System not ready. Please fix the issues above.", style="red")
        )
    elif "⚠️  WARN" in str(table):
        console.print(
            Panel(
                "⚠️  System ready with warnings. Consider configuring API keys.",
                style="yellow",
            )
        )
    else:
        console.print(
            Panel("✅ System ready! You can start using Capibara Core.", style="green")
        )

    # Installation instructions
    console.print("\n[bold]Quick Start:[/bold]")
    console.print("1. Configure API key: [cyan]export GROQ_API_KEY=your_key[/cyan]")
    console.print("2. Run example: [cyan]capibara run 'Hello World' --execute[/cyan]")
    console.print("3. View help: [cyan]capibara --help[/cyan]")

    # Docker installation help
    if "❌ FAIL" in str(table) and "Docker" in str(table):
        console.print("\n[bold]Docker Installation Help:[/bold]")
        console.print("• macOS: [cyan]brew install --cask docker[/cyan]")
        console.print("• Linux: [cyan]curl -fsSL https://get.docker.com | sh[/cyan]")
        console.print("• Windows: Download from https://docker.com")
        console.print("• Or run: [cyan]./scripts/install-docker.sh[/cyan]")


def _get_client(ctx: click.Context) -> CapibaraClient:
    """Get or create Capibara client."""
    if "client" not in ctx.obj:
        # Get API keys from environment
        openai_key = os.getenv("OPENAI_API_KEY")
        groq_key = os.getenv("GROQ_API_KEY")

        if not openai_key and not groq_key:
            console.print(
                "[bold red]Error:[/bold red] No API keys found. Set OPENAI_API_KEY or GROQ_API_KEY environment variables."
            )
            raise click.Abort()

        ctx.obj["client"] = CapibaraClient(
            openai_api_key=openai_key,
            groq_api_key=groq_key,
        )

    return ctx.obj["client"]  # type: ignore[no-any-return]


if __name__ == "__main__":
    cli()
