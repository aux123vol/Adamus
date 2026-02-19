"""
Genre Builder: Scaffolds Genre product features.

Genre products:
  - Lore    — AI-powered world-building / creative writing
  - Saga    — Payments and monetisation
  - Bible   — Collaborative knowledge base

"Build Genre 10x faster by being Augustus's AI CTO."
"""

import logging
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class GenreFeature:
    """A Genre product feature to scaffold."""
    name: str
    product: str        # lore / saga / bible
    description: str
    priority: int = 1   # 1 (highest) → 5 (lowest)
    status: str = "pending"     # pending / scaffolded / in_progress / done
    revenue_impact: str = "medium"  # low / medium / high (MRR north star)
    effort_days: float = 3.0


# Genre product roadmap (seed features)
GENRE_ROADMAP: List[GenreFeature] = [
    # Lore — AI world-building
    GenreFeature(
        name="lore_editor",
        product="lore",
        description="Rich-text editor for creative world-building with AI assist",
        priority=1,
        revenue_impact="high",
        effort_days=3,
    ),
    GenreFeature(
        name="lore_ai_assist",
        product="lore",
        description="AI co-writer that suggests plot/lore expansions",
        priority=2,
        revenue_impact="high",
        effort_days=4,
    ),
    GenreFeature(
        name="lore_collaboration",
        product="lore",
        description="Multi-user collaborative editing for Lore documents",
        priority=3,
        revenue_impact="medium",
        effort_days=5,
    ),

    # Saga — Payments
    GenreFeature(
        name="saga_subscriptions",
        product="saga",
        description="Stripe subscription billing for Genre plans",
        priority=1,
        revenue_impact="high",
        effort_days=2,
    ),
    GenreFeature(
        name="saga_usage_metering",
        product="saga",
        description="Track AI token usage per user for billing",
        priority=2,
        revenue_impact="high",
        effort_days=2,
    ),

    # Bible — Knowledge base
    GenreFeature(
        name="bible_search",
        product="bible",
        description="Full-text search across all Bible documents",
        priority=1,
        revenue_impact="medium",
        effort_days=2,
    ),
    GenreFeature(
        name="bible_ai_summary",
        product="bible",
        description="AI-generated summaries of Bible knowledge entries",
        priority=2,
        revenue_impact="medium",
        effort_days=3,
    ),
]

# File templates per product
_TEMPLATES: Dict[str, str] = {
    "lore": textwrap.dedent("""\
        \"\"\"
        {feature_name} — Lore Product Feature
        {description}

        Lore: AI-powered world-building and creative writing.
        Revenue impact: {revenue_impact}
        \"\"\"
        import logging
        from dataclasses import dataclass
        from typing import Optional

        logger = logging.getLogger(__name__)


        @dataclass
        class {class_name}Config:
            enabled: bool = True
            # TODO: Add configuration fields


        class {class_name}:
            \"\"\"
            {description}
            \"\"\"

            def __init__(self, config: Optional[{class_name}Config] = None):
                self.config = config or {class_name}Config()
                logger.info(f"{class_name} initialised")

            def health_check(self) -> dict:
                return {{"feature": "{feature_name}", "product": "lore", "active": True}}

            # TODO: Implement {feature_name}
    """),

    "saga": textwrap.dedent("""\
        \"\"\"
        {feature_name} — Saga Product Feature
        {description}

        Saga: Payments and monetisation.
        Revenue impact: {revenue_impact}
        \"\"\"
        import logging
        from dataclasses import dataclass
        from typing import Optional

        logger = logging.getLogger(__name__)


        @dataclass
        class {class_name}Config:
            enabled: bool = True
            # TODO: Add Stripe / billing configuration


        class {class_name}:
            \"\"\"
            {description}
            \"\"\"

            def __init__(self, config: Optional[{class_name}Config] = None):
                self.config = config or {class_name}Config()
                logger.info(f"{class_name} initialised")

            def health_check(self) -> dict:
                return {{"feature": "{feature_name}", "product": "saga", "active": True}}

            # TODO: Implement {feature_name}
    """),

    "bible": textwrap.dedent("""\
        \"\"\"
        {feature_name} — Bible Product Feature
        {description}

        Bible: Collaborative knowledge base.
        Revenue impact: {revenue_impact}
        \"\"\"
        import logging
        from dataclasses import dataclass
        from typing import Optional

        logger = logging.getLogger(__name__)


        @dataclass
        class {class_name}Config:
            enabled: bool = True
            # TODO: Add knowledge-base configuration


        class {class_name}:
            \"\"\"
            {description}
            \"\"\"

            def __init__(self, config: Optional[{class_name}Config] = None):
                self.config = config or {class_name}Config()
                logger.info(f"{class_name} initialised")

            def health_check(self) -> dict:
                return {{"feature": "{feature_name}", "product": "bible", "active": True}}

            # TODO: Implement {feature_name}
    """),
}


class GenreBuilder:
    """
    Scaffolds Genre product features.

    "Adamus multiplies Augustus 2.67x (24hr work from 9hr input)."
    """

    PRODUCTS = ["lore", "saga", "bible"]
    FEATURES_DIR = Path("src/genre")

    def __init__(self, base_path: Optional[Path] = None):
        self._base = base_path or Path(".")
        self._features_dir = self._base / self.FEATURES_DIR
        self._scaffolded: List[str] = []

    def scaffold_feature(self, feature: GenreFeature) -> Dict:
        """
        Scaffold a Genre feature module.
        Returns info about what was created.
        """
        if feature.product not in self.PRODUCTS:
            raise ValueError(f"Unknown product: {feature.product}. Must be one of {self.PRODUCTS}")

        product_dir = self._features_dir / feature.product
        product_dir.mkdir(parents=True, exist_ok=True)

        # Ensure __init__.py
        (product_dir / "__init__.py").touch()

        class_name = "".join(w.title() for w in feature.name.split("_"))
        template = _TEMPLATES.get(feature.product, _TEMPLATES["lore"])
        code = template.format(
            feature_name=feature.name,
            description=feature.description,
            revenue_impact=feature.revenue_impact,
            class_name=class_name,
        )

        out_path = product_dir / f"{feature.name}.py"
        out_path.write_text(code)

        feature.status = "scaffolded"
        self._scaffolded.append(feature.name)

        logger.info(f"Scaffolded: {feature.product}/{feature.name}")

        return {
            "feature": feature.name,
            "product": feature.product,
            "file": str(out_path.relative_to(self._base)),
            "class": class_name,
            "revenue_impact": feature.revenue_impact,
            "status": "scaffolded",
        }

    def get_roadmap(self, product: Optional[str] = None) -> List[Dict]:
        """Return Genre roadmap, optionally filtered by product."""
        items = GENRE_ROADMAP
        if product:
            items = [f for f in items if f.product == product]
        return [
            {
                "name": f.name,
                "product": f.product,
                "description": f.description,
                "priority": f.priority,
                "status": f.status,
                "revenue_impact": f.revenue_impact,
                "effort_days": f.effort_days,
            }
            for f in sorted(items, key=lambda f: (f.product, f.priority))
        ]

    def list_pending_features(self) -> List[str]:
        """Return names of pending (not scaffolded) features."""
        return [f.name for f in GENRE_ROADMAP if f.status == "pending"]

    def get_feature_template(self, product: str) -> str:
        """Return the code template for a product."""
        return _TEMPLATES.get(product, _TEMPLATES["lore"])

    def get_scaffolded(self) -> List[str]:
        return list(self._scaffolded)
