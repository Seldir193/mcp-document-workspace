import { TestBed } from '@angular/core/testing';

import { App } from './app';
import { WorkspaceApi } from './workspace-api.service';

const apiStub = {
  health: async () => ({ status: 'ready', server: 'document-workspace', transport: 'mcp-client' }),
  listDocuments: async () => [
    { id: 'release-notes', title: 'Release Notes 1.4', uri: 'docs://documents/release-notes' },
  ],
  getDocument: async () => ({
    id: 'release-notes',
    title: 'Release Notes 1.4',
    uri: 'docs://documents/release-notes',
    content: '# Release Notes 1.4',
  }),
  renderPrompt: async () => ({
    name: 'summarize' as const,
    doc_id: 'release-notes',
    text: 'Summarize this document',
  }),
  editDocument: async () => {
    throw new Error('Not used in this test');
  },
};

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [{ provide: WorkspaceApi, useValue: apiStub }],
    }).compileComponents();
  });

  it('creates the workspace', () => {
    const fixture = TestBed.createComponent(App);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('renders the project title', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h1')?.textContent).toContain('MCP Document Workspace');
  });

  it('loads MCP resources on startup', async () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Release Notes 1.4');
    expect(fixture.nativeElement.textContent).toContain('MCP server ready');
  });
});
