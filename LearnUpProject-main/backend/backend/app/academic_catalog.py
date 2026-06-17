"""Realistic Computer Science demo catalog used by backend seed scripts."""

from __future__ import annotations

import re
from dataclasses import dataclass


MAX_DEMO_SEMESTERS = 8


@dataclass(frozen=True)
class CatalogCourse:
    semester: int
    code: str
    title: str
    credit_hours: int = 3

    @property
    def level(self) -> int:
        return ((self.semester - 1) // 2) + 1


REALISTIC_COURSE_CATALOG: tuple[CatalogCourse, ...] = (
    CatalogCourse(1, "CS101", "Programming 1"),
    CatalogCourse(1, "CS102", "Computer Systems"),
    CatalogCourse(1, "MA101", "Calculus 1"),
    CatalogCourse(1, "HUM101", "Human Rights", 2),
    CatalogCourse(2, "CS103", "Programming 2"),
    CatalogCourse(2, "MA105", "Discrete Math"),
    CatalogCourse(2, "ENG101", "Technical Writing", 2),
    CatalogCourse(2, "PHY101", "Physics"),
    CatalogCourse(3, "CS201", "Data Structures"),
    CatalogCourse(3, "CS202", "Computer Architecture"),
    CatalogCourse(3, "MA201", "Linear Algebra"),
    CatalogCourse(3, "STAT201", "Probability and Statistics"),
    CatalogCourse(4, "CS203", "Object Oriented Programming"),
    CatalogCourse(4, "CS204", "Operating Systems"),
    CatalogCourse(4, "CS205", "Database Systems"),
    CatalogCourse(4, "SE201", "Software Engineering 1"),
    CatalogCourse(5, "CS301", "Algorithms"),
    CatalogCourse(5, "CS302", "Computer Networks"),
    CatalogCourse(5, "CS303", "Web Development"),
    CatalogCourse(5, "AI301", "Introduction to Artificial Intelligence"),
    CatalogCourse(6, "CS304", "Information Security"),
    CatalogCourse(6, "CS305", "Mobile Application Development"),
    CatalogCourse(6, "SE302", "Software Engineering 2"),
    CatalogCourse(6, "DS301", "Data Mining"),
    CatalogCourse(7, "CS401", "Machine Learning"),
    CatalogCourse(7, "CS402", "Cloud Computing"),
    CatalogCourse(7, "SE401", "Project Management"),
    CatalogCourse(7, "CS498", "Capstone 1"),
    CatalogCourse(8, "CS403", "Advanced Databases"),
    CatalogCourse(8, "CS404", "Distributed Systems"),
    CatalogCourse(8, "CS405", "Human Computer Interaction"),
    CatalogCourse(8, "CS499", "Capstone 2 / Graduation Project"),
)


COURSE_PREREQUISITES: dict[str, tuple[str, ...]] = {
    "CS103": ("CS101",),
    "CS201": ("CS103",),
    "CS202": ("CS102",),
    "CS203": ("CS103",),
    "CS204": ("CS202",),
    "CS205": ("CS201",),
    "SE201": ("CS103",),
    "CS301": ("CS201",),
    "CS302": ("CS202",),
    "CS303": ("CS103",),
    "AI301": ("CS201", "MA105"),
    "CS304": ("CS204",),
    "CS305": ("CS203",),
    "SE302": ("SE201",),
    "DS301": ("CS205", "STAT201"),
    "CS401": ("AI301", "MA201"),
    "CS402": ("CS302",),
    "SE401": ("SE302",),
    "CS498": ("SE302",),
    "CS403": ("CS205",),
    "CS404": ("CS302",),
    "CS405": ("CS303",),
    "CS499": ("CS498",),
}


_SEMESTER_RE = re.compile(r"\bsem(?:ester)?\.?\s*#?\s*(\d{1,3})\b", re.IGNORECASE)


def parse_semester_number(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)

    text = str(value).strip()
    if not text:
        return None
    if text.isdigit():
        return int(text)

    match = _SEMESTER_RE.search(text)
    return int(match.group(1)) if match else None


def is_demo_semester_number(value: object) -> bool:
    semester_number = parse_semester_number(value)
    return semester_number is not None and 1 <= semester_number <= MAX_DEMO_SEMESTERS
