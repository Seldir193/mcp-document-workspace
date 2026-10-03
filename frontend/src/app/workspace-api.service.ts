import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import {
  DocumentDetail,
  DocumentSummary,
  EditResponse,
  HealthResponse,
  PromptName,
  PromptResponse,
} from './models';

@Injectable({ providedIn: 'root' })
export class WorkspaceApi {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = 'http://127.0.0.1:8000/api';

  health(): Promise<HealthResponse> {
    return firstValueFrom(this.http.get<HealthResponse>(`${this.baseUrl}/health`));
  }

  listDocuments(): Promise<DocumentSummary[]> {
    return firstValueFrom(this.http.get<DocumentSummary[]>(`${this.baseUrl}/documents`));
  }

  getDocument(id: string): Promise<DocumentDetail> {
    return firstValueFrom(this.http.get<DocumentDetail>(`${this.baseUrl}/documents/${id}`));
  }

  renderPrompt(name: PromptName, docId: string): Promise<PromptResponse> {
    return firstValueFrom(
      this.http.post<PromptResponse>(`${this.baseUrl}/prompts/${name}`, { doc_id: docId })
    );
  }

  editDocument(id: string, oldText: string, newText: string): Promise<EditResponse> {
    return firstValueFrom(
      this.http.post<EditResponse>(`${this.baseUrl}/documents/${id}/edit`, {
        old_text: oldText,
        new_text: newText,
      })
    );
  }
}
