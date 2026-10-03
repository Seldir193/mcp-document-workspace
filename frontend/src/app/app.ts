import { Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ActivityEntry, DocumentDetail, DocumentSummary, PromptName, PromptResponse } from './models';
import { WorkspaceApi } from './workspace-api.service';

@Component({
  selector: 'app-root',
  imports: [FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App implements OnInit {
  private readonly api = inject(WorkspaceApi);

  readonly documents = signal<DocumentSummary[]>([]);
  readonly selected = signal<DocumentDetail | null>(null);
  readonly status = signal<'connecting' | 'ready' | 'error'>('connecting');
  readonly activity = signal<ActivityEntry[]>([]);
  readonly promptOutput = signal<PromptResponse | null>(null);
  readonly editing = signal(false);
  readonly busy = signal(false);
  readonly error = signal('');
  readonly draft = signal('');

  ngOnInit(): void {
    void this.bootstrap();
  }

  async selectDocument(id: string): Promise<void> {
    await this.run(async () => {
      const document = await this.api.getDocument(id);
      this.selected.set(document);
      this.promptOutput.set(null);
      this.editing.set(false);
      this.log('Resource read', document.uri);
    });
  }

  async runPrompt(name: PromptName): Promise<void> {
    const document = this.selected();
    if (!document) return;
    await this.run(async () => {
      const prompt = await this.api.renderPrompt(name, document.id);
      this.promptOutput.set(prompt);
      this.log('Prompt rendered', `${name} · ${document.id}`);
    });
  }

  startEdit(): void {
    const document = this.selected();
    if (!document) return;
    this.draft.set(document.content);
    this.editing.set(true);
  }

  cancelEdit(): void {
    this.editing.set(false);
    this.draft.set('');
  }

  async saveEdit(): Promise<void> {
    const document = this.selected();
    if (!document) return;
    await this.run(async () => {
      const result = await this.api.editDocument(document.id, document.content, this.draft());
      this.selected.set(result.document);
      this.editing.set(false);
      this.draft.set('');
      this.log('Tool called', `edit_document · ${document.id}`);
    });
  }

  private async bootstrap(): Promise<void> {
    try {
      await this.api.health();
      this.status.set('ready');
      const documents = await this.api.listDocuments();
      this.documents.set(documents);
      this.log('MCP connected', 'document-workspace');
      if (documents[0]) await this.selectDocument(documents[0].id);
    } catch (error) {
      this.status.set('error');
      this.setError(error);
    }
  }

  private async run(operation: () => Promise<void>): Promise<void> {
    this.busy.set(true);
    this.error.set('');
    try {
      await operation();
    } catch (error) {
      this.setError(error);
    } finally {
      this.busy.set(false);
    }
  }

  private setError(error: unknown): void {
    this.error.set(error instanceof Error ? error.message : 'Unexpected error');
  }

  private log(title: string, detail: string): void {
    this.activity.update(entries => [{ title, detail }, ...entries].slice(0, 6));
  }
}
