"""Add missing MoodConfig and MoodSnapshot models to shared/models.py."""

models_content = '''
class MoodConfig(Base):
    """Mood tracking configuration per group."""

    __tablename__ = "mood_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), unique=True)

    # Feature toggle
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Tracking settings
    tracking_period_hours: Mapped[int] = mapped_column(Integer, default=24)

    # Alert settings
    alert_negative_streak_days: Mapped[int] = mapped_column(Integer, default=3)
    alert_threshold: Mapped[float] = mapped_column(Integer, default=-0.3)
    notify_admins: Mapped[bool] = mapped_column(Boolean, default=True)

    # Reporting
    weekly_report: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


class MoodSnapshot(Base):
    """Mood tracking snapshots for groups."""

    __tablename__ = "mood_snapshots"
    __table_args__ = (
        UniqueConstraint("group_id", "period_start", name="uq_mood_snapshot_period"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)

    # Period
    period_start: Mapped[datetime] = mapped_column(DateTime, index=True)
    period_end: Mapped[datetime] = mapped_column(DateTime)

    # Sentiment metrics
    avg_sentiment: Mapped[float] = mapped_column(Integer, default=0)
    positive_ratio: Mapped[float] = mapped_column(Integer, default=0)
    negative_ratio: Mapped[float] = mapped_column(Integer, default=0)
    neutral_ratio: Mapped[float] = mapped_column(Integer, default=0)

    # Categorization
    mood_label: Mapped[str] = mapped_column(String(20), default="neutral")

    # Volume
    message_count: Mapped[int] = mapped_column(Integer, default=0)

    # Topics
    dominant_topics: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)

    # Alert state
    alert_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    alert_reason: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
'''

# Check if models already exist
with open("/home/engine/project/shared/models.py", "r") as f:
    content = f.read()

if "class MoodConfig" in content and "class MoodSnapshot" in content:
    print("Models already exist, skipping...")
else:
    # Find the insertion point (after MemberRetention)
    if "# ============ CHALLENGES MODELS ============" in content:
        insertion_point = content.find("# ============ CHALLENGES MODELS ============")
        new_content = content[:insertion_point] + models_content + "\n\n" + content[insertion_point:]
        with open("/home/engine/project/shared/models.py", "w") as f:
            f.write(new_content)
        print("Added MoodConfig and MoodSnapshot models to shared/models.py")
    else:
        print("Could not find insertion point, appending to end...")
        with open("/home/engine/project/shared/models.py", "a") as f:
            f.write("\n\n" + models_content)
        print("Appended MoodConfig and MoodSnapshot models to shared/models.py")
