import { Component, computed, signal } from '@angular/core';

type DocumentItem = {
  id: string;
  title: string;
  content: string;
};

@Component({
  selector: 'app-root',
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  readonly documents: DocumentItem[] = [
    { id: 'welcome.md', title: 'Welcome', content: 'MCP Document Workspace demonstrates tools, resources and prompts.' },
    { id: 'project-notes.md', title: 'Project Notes', content: 'Keep the project small, tested, documented and portfolio-ready.' }
  ];
  readonly selectedId = signal(this.documents[0].id);
  readonly selected = computed(
    () => this.documents.find(document => document.id === this.selectedId()) ?? this.documents[0]
  );

  selectDocument(id: string): void {
    this.selectedId.set(id);
  }
}
