from dataclasses import dataclass


@dataclass
class Document:
    id: str
    title: str
    content: str


DOCUMENTS: dict[str, Document] = {
    "welcome.md": Document(
        id="welcome.md",
        title="Welcome",
        content="MCP Document Workspace demonstrates tools, resources and prompts.",
    ),
    "project-notes.md": Document(
        id="project-notes.md",
        title="Project Notes",
        content="Keep the project small, tested, documented and portfolio-ready.",
    ),
}
