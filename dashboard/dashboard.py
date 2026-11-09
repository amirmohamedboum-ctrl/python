
"""
Dashboard professionnel - SSH Log Analysis
Thème sombre SOC / Cybersecurity
Bibliothèques : matplotlib, os, collections
"""

import os
from collections import Counter

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import MaxNLocator

from utils.logger import get_logger

logger = get_logger("dashboard")

TOP_N = 10

# Palette professionnelle
BACKGROUND = "#0B1120"
PANEL = "#151F32"
PANEL_LIGHT = "#1D2A40"
TEXT = "#F1F5F9"
MUTED = "#94A3B8"
BLUE = "#38BDF8"
GREEN = "#34D399"
RED = "#FB7185"
ORANGE = "#FBBF24"
GRID = "#29364D"


def create_kpi(ax, title, value, subtitle, color):
    """Crée une carte statistique."""

    ax.set_facecolor(BACKGROUND)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    card = FancyBboxPatch(
        (0.03, 0.05),
        0.94,
        0.90,
        boxstyle="round,pad=0.02,rounding_size=0.04",
        facecolor=PANEL,
        edgecolor=GRID,
        linewidth=1.2,
        transform=ax.transAxes
    )
    ax.add_patch(card)

    ax.text(
        0.10, 0.76, title,
        color=MUTED,
        fontsize=10,
        fontweight="bold",
        transform=ax.transAxes
    )

    ax.text(
        0.10, 0.43, f"{value:,}".replace(",", " "),
        color=color,
        fontsize=25,
        fontweight="bold",
        transform=ax.transAxes
    )

    ax.text(
        0.10, 0.18, subtitle,
        color=MUTED,
        fontsize=9,
        transform=ax.transAxes
    )


def bar_chart(ax, counter, title, xlabel, color):
    """Crée un graphique horizontal professionnel."""

    ax.set_facecolor(PANEL)
    ax.set_title(
        title,
        color=TEXT,
        fontsize=12,
        fontweight="bold",
        loc="left",
        pad=18
    )

    items = counter.most_common(TOP_N)

    if not items:
        ax.text(
            0.5, 0.5, "Aucune donnée disponible",
            color=MUTED,
            ha="center",
            va="center",
            transform=ax.transAxes
        )
        ax.set_xticks([])
        ax.set_yticks([])
        return

    labels = [
        str(name if name else "Unknown")
        for name, _ in items
    ][::-1]

    values = [value for _, value in items][::-1]

    bars = ax.barh(
        labels,
        values,
        color=color,
        height=0.55,
        alpha=0.9
    )

    ax.bar_label(
        bars,
        padding=6,
        color=TEXT,
        fontsize=9,
        fontweight="bold"
    )

    ax.set_xlabel(xlabel, color=MUTED, fontsize=9)
    ax.tick_params(axis="x", colors=MUTED, labelsize=8)
    ax.tick_params(axis="y", colors=TEXT, labelsize=9)

    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(axis="x", color=GRID, linestyle="--", alpha=0.7)
    ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(GRID)

    ax.margins(x=0.18)


def summary_panel(ax, failed, success, invalid, countries):
    """Affiche un résumé de sécurité."""

    ax.set_facecolor(PANEL)
    ax.axis("off")

    ax.set_title(
        "SECURITY OVERVIEW",
        color=TEXT,
        fontsize=12,
        fontweight="bold",
        loc="left",
        pad=18
    )

    total = failed + success

    success_rate = (
        success / total * 100 if total > 0 else 0
    )

    failed_rate = (
        failed / total * 100 if total > 0 else 0
    )

    lines = [
        ("Total des tentatives", total, BLUE),
        ("Taux de réussite", f"{success_rate:.1f} %", GREEN),
        ("Taux d'échec", f"{failed_rate:.1f} %", RED),
        ("Échecs avec utilisateur invalide", invalid, ORANGE),
        ("Pays concernés par les échecs", countries, BLUE)
    ]

    y = 0.83

    for label, value, color in lines:
        ax.text(
            0.04, y, label,
            color=MUTED,
            fontsize=10,
            transform=ax.transAxes
        )

        ax.text(
            0.96, y, str(value),
            color=color,
            fontsize=11,
            fontweight="bold",
            ha="right",
            transform=ax.transAxes
        )

        y -= 0.17


def build_dashboard(
    by_country: Counter,
    success_by_user: Counter,
    invalid_users: Counter,
    output_path: str,
    show: bool = True
) -> None:
    """Construit et enregistre le dashboard professionnel."""

    try:
        failed_total = sum(by_country.values())
        success_total = sum(success_by_user.values())
        invalid_total = sum(invalid_users.values())

        total_attempts = failed_total + success_total

        fig = plt.figure(
            figsize=(16, 10),
            facecolor=BACKGROUND
        )

        fig.suptitle(
            "SSH LOG ANALYSIS | SECURITY OPERATIONS CENTER",
            fontsize=19,
            fontweight="bold",
            color=TEXT,
            y=0.97
        )

        fig.text(
            0.5, 0.935,
            "Authentication monitoring • Threat analysis • Security statistics",
            color=MUTED,
            fontsize=10,
            ha="center"
        )

        gs = fig.add_gridspec(
            3, 4,
            left=0.06,
            right=0.96,
            top=0.88,
            bottom=0.09,
            hspace=0.55,
            wspace=0.35,
            height_ratios=[0.9, 2, 2]
        )

        # 1. Cartes KPI
        kpi_data = [
            ("TOTAL ATTEMPTS", total_attempts, "All authentication events", BLUE),
            ("FAILED LOGINS", failed_total, "Failed authentication", RED),
            ("SUCCESSFUL LOGINS", success_total, "Successful authentication", GREEN),
            ("INVALID USERS", invalid_total, "Invalid user failures", ORANGE)
        ]

        for i, data in enumerate(kpi_data):
            ax = fig.add_subplot(gs[0, i])
            create_kpi(ax, *data)

        # 2. Graphique des échecs par pays
        ax1 = fig.add_subplot(gs[1, 0:2])
        bar_chart(
            ax1,
            by_country,
            "FAILED ATTEMPTS BY COUNTRY",
            "Number of attempts",
            RED
        )

        # 3. Connexions réussies par utilisateur
        ax2 = fig.add_subplot(gs[1, 2:4])
        bar_chart(
            ax2,
            success_by_user,
            "SUCCESSFUL LOGINS BY USER",
            "Number of connections",
            GREEN
        )

        # 4. Utilisateurs invalides
        ax3 = fig.add_subplot(gs[2, 0:2])
        bar_chart(
            ax3,
            invalid_users,
            "INVALID USER ATTEMPTS",
            "Number of attempts",
            ORANGE
        )

        # 5. Résumé de sécurité
        ax4 = fig.add_subplot(gs[2, 2:4])
        summary_panel(
            ax4,
            failed_total,
            success_total,
            invalid_total,
            len(by_country)
        )

        fig.text(
            0.5, 0.025,
            "SSH LOG ANALYSIS PROJECT | PostgreSQL + Python + Matplotlib",
            color=MUTED,
            fontsize=9,
            ha="center"
        )

        os.makedirs(
            os.path.dirname(output_path) or ".",
            exist_ok=True
        )

        fig.savefig(
            output_path,
            dpi=160,
            facecolor=BACKGROUND,
            bbox_inches="tight"
        )

        logger.info(
            "Dashboard professionnel enregistré : %s",
            output_path
        )

        if show:
            plt.show()

        plt.close(fig)

    except OSError as e:
        logger.error(
            "Impossible d'enregistrer le dashboard : %s", e
        )

    except Exception:
        logger.exception(
            "Erreur lors de la construction du dashboard"
        )
        raise
