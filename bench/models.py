from django.db import models


class Metric(models.Model):
    """
    Stores one CI/CD pipeline run's metrics and context.

    This is the core data structure for your research:
    - Which tool (GitHub Actions / Jenkins / CodePipeline)
    - Which workflow / run / branch / commit
    - Novel metrics: LCE, PRT, SMO, DEPT, CLBC
    """

    # ---- Source (which CI/CD tool) ----
    SOURCE_GITHUB = "github"
    SOURCE_JENKINS = "jenkins"
    SOURCE_CODEPIPELINE = "codepipeline"

    SOURCE_CHOICES = [
        (SOURCE_GITHUB, "GitHub Actions"),
        (SOURCE_JENKINS, "Jenkins"),
        (SOURCE_CODEPIPELINE, "AWS CodePipeline"),
    ]

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when this metric entry was stored.",
    )

    source = models.CharField(
        max_length=32,
        choices=SOURCE_CHOICES,
        default=SOURCE_GITHUB,
        help_text="CI/CD platform that produced this run.",
    )

    # ---- CI/CD context ----
    workflow = models.CharField(
        max_length=128,
        blank=True,
        default="",
        help_text="Name of workflow/job (e.g. GitHub workflow name or Jenkins job).",
    )
    run_id = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Unique run/build ID from the CI/CD tool.",
    )
    run_attempt = models.CharField(
        max_length=16,
        blank=True,
        default="",
        help_text="Attempt number for this run (if the tool supports retries).",
    )
    branch = models.CharField(
        max_length=128,
        blank=True,
        default="",
        help_text="Git branch name for this run.",
    )
    commit_sha = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Git commit SHA for this run.",
    )

    # ---- Novel metrics ----
    lce = models.FloatField(
        default=0.0,
        help_text="Layer Cache Efficiency – how effectively Docker cache was reused.",
    )
    prt = models.FloatField(
        default=0.0,
        help_text="Pipeline Recovery Time – time to recover from a failing run to a successful one.",
    )
    smo = models.FloatField(
        default=0.0,
        help_text="Secrets Management Overhead – time/latency introduced by secrets handling.",
    )
    dept = models.FloatField(
        default=0.0,
        help_text="Dynamic Environment Provisioning Time – time Terraform takes to spin up/tear down infra.",
    )
    clbc = models.FloatField(
        default=0.0,
        help_text="Cross-Layer Build Consistency – consistency of Docker image layers across runs/tools.",
    )

    notes = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Optional notes (e.g., scenario type: clean build, cache warm, failure-recovery, etc.).",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Metric"
        verbose_name_plural = "Metrics"

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M:%S} | {self.get_source_display()} | {self.branch} | {self.commit_sha[:7]}"
