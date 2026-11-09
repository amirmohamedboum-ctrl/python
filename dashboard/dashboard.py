"""
Module dashboard : affichage des 3 indicateurs demandés avec matplotlib.

  1. nombre de tentatives échouées par pays
  2. nombre de tentatives réussies par utilisateur
  3. tentatives échouées avec invalid user (par nom d'utilisateur)
  + un panneau de chiffres clés

Le dashboard est enregistré en PNG puis affiché.
"""
import os
from collections import Counter

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from utils.logger import get_logger

logger = get_logger("dashboard")

TOP_N = 10


def _bar_chart(ax, counter: Counter, title: str, xlabel: str) -> None:
    """Diagramme en barres horizontales des TOP_N valeurs du compteur."""
    ax.set_title(title, fontweight="bold")
    items = counter.most_common(TOP_N)
    if not items:
        logger.warning("Pas de données pour le graphique : %s", title)
        ax.text(0.5, 0.5, "Aucune donnée", ha="center", va="center", transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        return

    labels = [name for name, _ in items][::-1]   # le plus grand en haut
    values = [value for _, value in items][::-1]
    bars = ax.barh(labels, values)
    ax.bar_label(bars, padding=3)
    ax.set_xlabel(xlabel)
    ax.margins(x=0.12)
    ax.set_ylim(-0.5, max(len(items), 4) - 0.5)       # évite une barre géante s'il y a peu de valeurs
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))  # pas de décimales


def build_dashboard(by_country: Counter, success_by_user: Counter, invalid_users: Counter,
                    output_path: str, show: bool = True) -> None:
    """Construit le dashboard, l'enregistre dans output_path et l'affiche."""
    try:
        fig, axes = plt.subplots(2, 2, figsize=(15, 9))
        fig.suptitle("Dashboard - analyse des logs SSH (auth.log)", fontsize=16, fontweight="bold")

        _bar_chart(axes[0][0], by_country, f"Tentatives échouées par pays (top {TOP_N})", "Tentatives")
        _bar_chart(axes[0][1], success_by_user, "Tentatives réussies par utilisateur", "Connexions")
        _bar_chart(axes[1][0], invalid_users, f"Échecs avec 'invalid user' (top {TOP_N})", "Tentatives")

        # Panneau de chiffres clés
        ax = axes[1][1]
        ax.axis("off")
        ax.set_title("Chiffres clés", fontweight="bold")
        kpis = (
            f"Tentatives échouées : {sum(by_country.values())}\n\n"
            f"Tentatives réussies : {sum(success_by_user.values())}\n\n"
            f"Échecs 'invalid user' : {sum(invalid_users.values())}\n\n"
            f"Pays différents : {len(by_country)}\n\n"
            f"Noms d'utilisateur invalides : {len(invalid_users)}"
        )
        ax.text(0.05, 0.9, kpis, va="top", fontsize=13, transform=ax.transAxes)

        fig.tight_layout()

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fig.savefig(output_path, dpi=120)
        logger.info("Dashboard enregistré : %s", output_path)

        if show:
            plt.show()
        plt.close(fig)
    except OSError as e:
        logger.error("Impossible d'enregistrer le dashboard %s : %s", output_path, e)
    except Exception:
        logger.exception("Erreur lors de la construction du dashboard")