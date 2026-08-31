import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface TheoryMove {
  uci: string;
  san: string;
  white: number;
  draws: number;
  black: number;
  popularity: number;
}

export interface ContextResult {
  title: string;
  text: string;
  source_url: string;
  score: number;
}

export interface VideoResult {
  video_id: string;
  title: string;
  channel: string;
  thumbnail_url: string;
  url: string;
}

export interface AgentResponse {
  fen: string;
  route: 'theory' | 'engine';
  summary: string;
  opening: { eco?: string; name?: string } | null;
  suggested_moves: TheoryMove[];
  evaluation: {
    centipawns: number | null;
    mate_in: number | null;
    best_move: string | null;
  } | null;
  context: ContextResult[];
  videos: VideoResult[];
  warnings: string[];
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly baseUrl = '/api/v1';

  constructor(private readonly http: HttpClient) {}

  analyze(fen: string): Observable<AgentResponse> {
    return this.http.post<AgentResponse>(`${this.baseUrl}/agent/analyze`, { fen });
  }
}

