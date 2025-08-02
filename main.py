#!/usr/bin/env python3
"""
Techronicle AutoGen - Main CLI Application
Command-line interface for running newsroom sessions
"""

import sys
import os
import time
import json
from datetime import datetime
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.newsroom import TechronicleNewsroom
from utils.config import config
from utils.logger import get_logger

# Initialize CLI
app = typer.Typer(help="Techronicle AutoGen - Multi-Agent Crypto News Curation")
console = Console()

def display_banner():
    """Display the application banner"""
    banner = """
    ████████╗███████╗ ██████╗██╗  ██╗██████╗  ██████╗ ███╗   ██╗██╗ ██████╗██╗     ███████╗
    ╚══██╔══╝██╔════╝██╔════╝██║  ██║██╔══██╗██╔═══██╗████╗  ██║██║██╔════╝██║     ██╔════╝
       ██║   █████╗  ██║     ███████║██████╔╝██║   ██║██╔██╗ ██║██║██║     ██║     █████╗  
       ██║   ██╔══╝  ██║     ██╔══██║██╔══██╗██║   ██║██║╚██╗██║██║██║     ██║     ██╔══╝  
       ██║   ███████╗╚██████╗██║  ██║██║  ██║╚██████╔╝██║ ╚████║██║╚██████╗███████╗███████╗
       ╚═╝   ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝ ╚═════╝╚══════╝╚══════╝
    """
    
    console.print(Panel(
        f"[bold cyan]{banner}[/bold cyan]\n\n"
        "[bold white]Multi-Agent Crypto News Curation System[/bold white]\n"
        "[dim]Powered by AutoGen Framework[/dim]",
        title="🚀 Techronicle AutoGen",
        border_style="cyan"
    ))

def check_configuration():
    """Check if the system is properly configured"""
    issues = []
    
    if not config.openai_api_key:
        issues.append("❌ OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
    
    if not config.rss_feeds:
        issues.append("❌ No RSS feeds configured.")
    
    if issues:
        console.print(Panel(
            "\n".join(issues) + "\n\n[yellow]Please check your configuration before running.[/yellow]",
            title="⚠️ Configuration Issues",
            border_style="red"
        ))
        return False
    
    console.print("[green]✅ Configuration looks good![/green]")
    return True

def display_team_info():
    """Display information about the newsroom team"""
    team_table = Table(title="🤖 Newsroom Team")
    team_table.add_column("Agent", style="cyan", no_wrap=True)
    team_table.add_column("Role", style="magenta")
    team_table.add_column("Age", justify="center")
    team_table.add_column("Background", style="green")
    team_table.add_column("Specialty", style="yellow")
    
    team_members = [
        ("Gary Poussin", "Beat Reporter", "28", "Ex-CoinDesk, Northwestern", "Breaking news, sources"),
        ("Aravind Rajen", "Market Analyst", "34", "PhD MIT, Ex-Goldman", "On-chain analysis, DeFi"),
        ("Tijana Jekic", "Copy Editor", "31", "Ex-Reuters, Columbia", "Fact-checking, compliance"),
        ("Jerin Sojan", "Managing Editor", "38", "Ex-WSJ, Wharton MBA", "Editorial strategy"),
        ("Aayushi Patel", "Audience Editor", "26", "Ex-BuzzFeed, NYU", "Growth, engagement"),
        ("Sarah Donato", "Publishing Manager", "29", "Tech startups, UC Berkeley", "Distribution, optimization")
    ]
    
    for agent, role, age, background, specialty in team_members:
        team_table.add_row(agent, role, age, background, specialty)
    
    console.print(team_table)

@app.command()
def run(
    articles: int = typer.Option(5, "--articles", "-a", help="Maximum articles to discuss"),
    session_id: Optional[str] = typer.Option(None, "--session", "-s", help="Custom session ID"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive mode with prompts"),
    save: bool = typer.Option(True, "--save/--no-save", help="Save conversation to file")
):
    """Run a complete editorial session"""
    
    display_banner()
    
    if not check_configuration():
        raise typer.Exit(code=1)
    
    if interactive:
        console.print("\n[bold]🎛️ Interactive Mode[/bold]")
        articles = int(Prompt.ask("How many articles to discuss?", default="5"))
        
        if Confirm.ask("Show team information?"):
            display_team_info()
    
    console.print(f"\n[bold green]🚀 Starting Editorial Session[/bold green]")
    console.print(f"📊 Max articles: {articles}")
    console.print(f"💾 Save conversation: {save}")
    
    try:
        # Initialize newsroom
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            init_task = progress.add_task("Initializing newsroom agents...", total=None)
            newsroom = TechronicleNewsroom(session_id=session_id)
            progress.update(init_task, completed=True)
            
            # Run editorial session
            session_task = progress.add_task("Running editorial discussion...", total=None)
            results = newsroom.run_editorial_session(max_articles=articles)
            progress.update(session_task, completed=True)
        
        # Display results
        if results["success"]:
            console.print(f"\n[bold green]🎉 Session Completed Successfully![/bold green]")
            
            # Results summary
            summary_table = Table(title="📊 Session Summary")
            summary_table.add_column("Metric", style="cyan")
            summary_table.add_column("Value", style="green")
            
            summary_table.add_row("Session ID", results["session_id"])
            summary_table.add_row("Articles Discussed", str(results["articles_discussed"]))
            summary_table.add_row("Articles Approved", str(results["articles_approved"]))
            summary_table.add_row("Articles Published", str(results["articles_published"]))
            summary_table.add_row("Total Messages", str(results["total_messages"]))
            summary_table.add_row("Decisions Made", str(len(results["decisions_made"])))
            summary_table.add_row("Participants", str(len(results["participants"])))
            summary_table.add_row("Publication Req. Met", "✅ Yes" if results["publication_requirement_met"] else "❌ No")
            
            console.print(summary_table)
            
            # Show published articles
            if results.get("approved_articles"):
                console.print(f"\n[bold]📰 Published Articles:[/bold]")
                for i, article in enumerate(results["approved_articles"], 1):
                    console.print(f"{i}. [green]{article['title']}[/green]")
                    console.print(f"   Source: {article['source']}")
                    console.print(f"   Summary: {article['summary'][:100]}...")
                    console.print()
            
            # Show key decisions
            if results["decisions_made"]:
                console.print(f"\n[bold]📋 Editorial Decisions:[/bold]")
                for i, decision in enumerate(results["decisions_made"], 1):
                    decision_type = "🔴 OVERRIDE" if decision.get("metadata", {}).get("override") else "✅ STANDARD"
                    console.print(f"{i}. {decision_type} [cyan]{decision['decision_maker']}[/cyan]: {decision['content'][:100]}...")
            
            # Save option
            if save:
                saved_file = newsroom.save_session()
                console.print(f"\n[green]💾 {saved_file}[/green]")
            
            # Export options
            if interactive and Confirm.ask("\nExport conversation?"):
                format_choice = Prompt.ask("Export format", choices=["json", "markdown", "text"], default="markdown")
                
                export_content = newsroom.export_session(format_choice)
                export_filename = f"session_{results['session_id']}.{format_choice}"
                
                with open(export_filename, 'w') as f:
                    f.write(export_content)
                
                console.print(f"[green]📄 Exported to {export_filename}[/green]")
        
        else:
            console.print(f"[red]❌ Session failed: {results['error']}[/red]")
            raise typer.Exit(code=1)
    
    except KeyboardInterrupt:
        console.print(f"\n[yellow]⚠️ Session interrupted by user[/yellow]")
        raise typer.Exit(code=0)
    
    except Exception as e:
        console.print(f"[red]💥 Unexpected error: {e}[/red]")
        raise typer.Exit(code=1)

@app.command()
def team():
    """Display information about the newsroom team"""
    display_banner()
    display_team_info()
    
    console.print(f"\n[bold]🎭 Personality Highlights:[/bold]")
    
    personalities = [
        ("Gary", "🏃‍♂️ Hustler mentality, always chasing scoops, uses crypto slang"),
        ("Aravind", "🧠 PhD economist, methodical analysis, data-driven decisions"),
        ("Tijana", "✏️ Former Reuters editor, fact-checking obsessed, risk-aware"),
        ("Jerin", "⚖️ WSJ veteran, diplomatic leadership, strategic thinking"),
        ("Aayushi", "📱 BuzzFeed background, crypto Twitter native, growth-focused"),
        ("Sarah", "🚀 Tech startup experience, optimization-focused, systems thinking")
    ]
    
    for name, description in personalities:
        console.print(f"• [cyan]{name}[/cyan]: {description}")

@app.command()
def config_check():
    """Check system configuration and requirements"""
    display_banner()
    
    console.print("[bold]🔧 Configuration Check[/bold]\n")
    
    # API Keys
    console.print("[bold]API Configuration:[/bold]")
    console.print(f"• OpenAI API Key: {'✅ Set' if config.openai_api_key else '❌ Missing'}")
    console.print(f"• OpenAI Model: {config.openai_model}")
    
    if config.serper_api_key:
        console.print(f"• Serper API Key: ✅ Set (optional)")
    
    # RSS Feeds
    console.print(f"\n[bold]RSS Feeds ({len(config.rss_feeds)} configured):[/bold]")
    for i, feed in enumerate(config.rss_feeds, 1):
        console.print(f"• {i}. {feed}")
    
    # Directories
    console.print(f"\n[bold]Storage Directories:[/bold]")
    directories = [
        ("Conversations", config.conversations_dir),
        ("Articles", config.articles_dir),
        ("Decisions", config.decisions_dir),
        ("Published", config.published_dir)
    ]
    
    for name, path in directories:
        exists = "✅" if path.exists() else "❌"
        console.print(f"• {name}: {exists} {path}")
    
    # Settings
    console.print(f"\n[bold]Session Settings:[/bold]")
    console.print(f"• Max Articles: {config.max_articles_per_session}")
    console.print(f"• Max Rounds: {config.max_rounds}")
    console.print(f"• Timeout: {config.conversation_timeout}s")
    console.print(f"• Save Conversations: {config.save_conversations}")

@app.command()
def demo():
    """Run a demo session with mock data"""
    display_banner()
    
    console.print("[bold yellow]🎪 Demo Mode[/bold yellow]")
    console.print("Running demonstration with mock crypto news articles...\n")
    
    # Force using mock articles
    original_feeds = config.rss_feeds
    config.rss_feeds = []  # This will force mock articles
    
    try:
        newsroom = TechronicleNewsroom(session_id=f"demo_{datetime.now().strftime('%H%M%S')}")
        results = newsroom.run_editorial_session(max_articles=3)
        
        if results["success"]:
            console.print("[bold green]🎉 Demo completed successfully![/bold green]")
            console.print(f"Session ID: {results['session_id']}")
            console.print(f"Messages exchanged: {results['total_messages']}")
            console.print(f"Articles published: {results.get('articles_published', 0)}")
        else:
            console.print(f"[red]❌ Demo failed: {results['error']}[/red]")
    
    finally:
        # Restore original feeds
        config.rss_feeds = original_feeds

@app.command()
def analyze(
    session_id: str = typer.Argument(..., help="Session ID to analyze"),
    export: bool = typer.Option(False, "--export", "-e", help="Export analysis to file")
):
    """Analyze a completed editorial session"""
    display_banner()
    
    try:
        # Load session
        from utils.logger import ConversationLogger
        logger = ConversationLogger()
        
        if not logger.load_conversation(session_id):
            console.print(f"[red]❌ Session {session_id} not found[/red]")
            raise typer.Exit(code=1)
        
        # Get analytics
        summary = logger.get_conversation_summary()
        
        console.print(f"[bold]📊 Session Analysis: {session_id}[/bold]\n")
        
        # Basic stats
        stats_table = Table(title="Session Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")
        
        stats = summary["stats"]
        stats_table.add_row("Total Messages", str(stats["total_messages"]))
        stats_table.add_row("Participants", str(stats["participants"]))
        stats_table.add_row("Duration (minutes)", str(stats["duration_minutes"]))
        stats_table.add_row("Most Active Speaker", stats["most_active_speaker"])
        
        console.print(stats_table)
        
        # Message types
        if stats.get("message_types"):
            console.print(f"\n[bold]📝 Message Types:[/bold]")
            for msg_type, count in stats["message_types"].items():
                console.print(f"• {msg_type}: {count}")
        
        # Decisions made
        if summary["metadata"]["decisions"]:
            console.print(f"\n[bold]📋 Editorial Decisions:[/bold]")
            for i, decision in enumerate(summary["metadata"]["decisions"], 1):
                console.print(f"{i}. [cyan]{decision['decision_maker']}[/cyan]: {decision['decision'][:80]}...")
        
        # Topics discussed
        if summary["metadata"]["topics"]:
            console.print(f"\n[bold]🏷️ Topics Discussed:[/bold]")
            for topic in summary["metadata"]["topics"]:
                console.print(f"• {topic}")
        
        # Export option
        if export:
            export_filename = f"analysis_{session_id}.json"
            with open(export_filename, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            console.print(f"\n[green]📄 Analysis exported to {export_filename}[/green]")
    
    except Exception as e:
        console.print(f"[red]❌ Error analyzing session: {e}[/red]")
        raise typer.Exit(code=1)

@app.command()
def list_sessions(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of sessions to show"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: table, json")
):
    """List recent editorial sessions"""
    display_banner()
    
    try:
        import glob
        
        # Find session files
        session_files = glob.glob(str(config.conversations_dir / "conversation_*.json"))
        session_files.sort(key=os.path.getmtime, reverse=True)  # Most recent first
        
        if not session_files:
            console.print("[yellow]No sessions found[/yellow]")
            return
        
        sessions_data = []
        
        for file_path in session_files[:limit]:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Extract session info
                session_info = {
                    "session_id": data["session_metadata"]["session_id"],
                    "started_at": data["session_metadata"]["started_at"],
                    "participants": len(data["session_metadata"]["participants"]),
                    "messages": len(data["messages"]),
                    "decisions": len(data["session_metadata"]["decisions"]),
                    "file_path": file_path
                }
                sessions_data.append(session_info)
                
            except Exception as e:
                console.print(f"[yellow]Warning: Could not read {file_path}: {e}[/yellow]")
                continue
        
        if format == "json":
            console.print(json.dumps(sessions_data, indent=2, default=str))
        else:
            # Table format
            sessions_table = Table(title=f"Recent Editorial Sessions (Last {len(sessions_data)})")
            sessions_table.add_column("Session ID", style="cyan")
            sessions_table.add_column("Started At", style="green")
            sessions_table.add_column("Participants", justify="center")
            sessions_table.add_column("Messages", justify="center")
            sessions_table.add_column("Decisions", justify="center")
            
            for session in sessions_data:
                started_time = session["started_at"].split("T")[1][:8] if "T" in session["started_at"] else "Unknown"
                sessions_table.add_row(
                    session["session_id"],
                    started_time,
                    str(session["participants"]),
                    str(session["messages"]),
                    str(session["decisions"])
                )
            
            console.print(sessions_table)
    
    except Exception as e:
        console.print(f"[red]❌ Error listing sessions: {e}[/red]")
        raise typer.Exit(code=1)

@app.command()
def export_session(
    session_id: str = typer.Argument(..., help="Session ID to export"),
    format: str = typer.Option("markdown", "--format", "-f", help="Export format: json, markdown, text"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path")
):
    """Export a session conversation in various formats"""
    display_banner()
    
    try:
        # Load session
        from utils.logger import ConversationLogger
        logger = ConversationLogger()
        
        if not logger.load_conversation(session_id):
            console.print(f"[red]❌ Session {session_id} not found[/red]")
            raise typer.Exit(code=1)
        
        # Export conversation
        export_content = logger.export_conversation(format)
        
        # Determine output file
        if not output:
            extension = {"json": "json", "markdown": "md", "text": "txt"}[format]
            output = f"session_{session_id}.{extension}"
        
        # Write to file
        with open(output, 'w') as f:
            f.write(export_content)
        
        console.print(f"[green]✅ Session exported to {output}[/green]")
        console.print(f"Format: {format}")
        console.print(f"Size: {len(export_content)} characters")
    
    except Exception as e:
        console.print(f"[red]❌ Error exporting session: {e}[/red]")
        raise typer.Exit(code=1)

@app.command()
def interactive():
    """Run interactive newsroom session with live updates"""
    display_banner()
    
    console.print("[bold yellow]🎮 Interactive Newsroom Mode[/bold yellow]")
    console.print("This mode provides step-by-step control over the editorial process.\n")
    
    if not check_configuration():
        raise typer.Exit(code=1)
    
    try:
        # Get session parameters
        console.print("[bold]📋 Session Setup[/bold]")
        
        custom_session_id = Prompt.ask("Custom session ID (or press enter for auto)", default="")
        session_id = custom_session_id if custom_session_id else None
        
        articles_count = int(Prompt.ask("Number of articles to discuss", default="5"))
        
        show_team = Confirm.ask("Show team information before starting?", default=True)
        if show_team:
            display_team_info()
        
        console.print(f"\n[bold green]🚀 Starting Interactive Session[/bold green]")
        
        # Initialize newsroom
        newsroom = TechronicleNewsroom(session_id=session_id)
        
        console.print(f"Session ID: {newsroom.session_id}")
        console.print("Initializing agents... ✅")
        
        # Collect articles
        console.print(f"\n[bold]📰 Collecting Articles[/bold]")
        articles = newsroom._prepare_articles(articles_count)
        
        console.print(f"Found {len(articles)} articles:")
        for i, article in enumerate(articles, 1):
            console.print(f"{i}. {article['title']} ({article['source']})")
        
        if not Confirm.ask("\nProceed with these articles?", default=True):
            console.print("[yellow]Session cancelled[/yellow]")
            return
        
        # Run discussion
        console.print(f"\n[bold]💬 Starting Editorial Discussion[/bold]")
        console.print("Agents are now discussing... (this may take a few minutes)")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Running editorial discussion...", total=None)
            
            results = newsroom.run_editorial_session(articles_count)
            progress.update(task, completed=True)
        
        # Display results
        if results["success"]:
            console.print(f"\n[bold green]🎉 Session Completed![/bold green]")
            
            # Quick summary
            console.print(f"📊 Messages: {results['total_messages']}")
            console.print(f"📰 Published: {results['articles_published']}")
            console.print(f"⏱️ Session: {newsroom.session_id}")
            
            # Show published articles
            if results.get("approved_articles"):
                console.print(f"\n[bold]📰 Published Articles:[/bold]")
                for article in results["approved_articles"]:
                    console.print(f"• [green]{article['title']}[/green]")
            
            # Post-session options
            console.print(f"\n[bold]📋 Post-Session Options[/bold]")
            
            if Confirm.ask("View conversation analysis?"):
                summary = newsroom.logger.get_conversation_summary()
                console.print(f"\nDuration: {summary['stats']['duration_minutes']} minutes")
                console.print(f"Most active: {summary['stats']['most_active_speaker']}")
            
            if Confirm.ask("Export conversation?"):
                export_format = Prompt.ask("Export format", choices=["json", "markdown", "text"], default="markdown")
                export_filename = f"session_{newsroom.session_id}.{export_format}"
                
                with open(export_filename, 'w') as f:
                    f.write(newsroom.export_session(export_format))
                
                console.print(f"[green]📄 Exported to {export_filename}[/green]")
        
        else:
            console.print(f"[red]❌ Session failed: {results['error']}[/red]")
    
    except KeyboardInterrupt:
        console.print(f"\n[yellow]⚠️ Session interrupted[/yellow]")
    except Exception as e:
        console.print(f"[red]💥 Error: {e}[/red]")

@app.command()
def version():
    """Show version information"""
    console.print(Panel(
        "[bold cyan]Techronicle AutoGen v1.0.0[/bold cyan]\n\n"
        "Multi-Agent Crypto News Curation System\n"
        "Built with AutoGen Framework\n\n"
        "[dim]Components:[/dim]\n"
        "• 6 AI agents with rich personalities\n"
        "• Real-time RSS feed collection\n"
        "• Collaborative editorial discussions\n"
        "• Guaranteed publication workflow\n"
        "• Comprehensive conversation logging",
        title="📦 Version Info",
        border_style="cyan"
    ))

def main():
    """Main entry point with error handling"""
    try:
        app()
    except KeyboardInterrupt:
        console.print(f"\n[yellow]👋 Goodbye![/yellow]")
    except Exception as e:
        console.print(f"[red]💥 Unexpected error: {e}[/red]")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    main()