import { Component, ViewChild } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { NgxChessBoardView } from 'ngx-chess-board';

import { AgentResponse, ApiService } from './api.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
})
export class AppComponent {
  @ViewChild('board', { static: false }) board?: NgxChessBoardView;

  readonly initialFen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
  fen = this.initialFen;
  loading = false;
  error = '';
  response?: AgentResponse;

  constructor(private readonly api: ApiService) {}

  onMove(): void {
    if (this.board) {
      this.fen = this.board.getFEN();
    }
    this.response = undefined;
  }

  loadFen(): void {
    this.error = '';
    try {
      this.board?.setFEN(this.fen.trim());
      this.fen = this.board?.getFEN() ?? this.fen;
      this.response = undefined;
    } catch {
      this.error = 'Cette position FEN ne peut pas être chargée.';
    }
  }

  reset(): void {
    this.board?.reset();
    this.fen = this.initialFen;
    this.response = undefined;
    this.error = '';
  }

  analyze(): void {
    this.fen = this.board?.getFEN() ?? this.fen;
    this.loading = true;
    this.error = '';
    this.response = undefined;
    this.api.analyze(this.fen).subscribe({
      next: (response) => {
        this.response = response;
        this.loading = false;
      },
      error: (error: HttpErrorResponse) => {
        this.error = error.error?.detail ?? 'Le coach ne répond pas. Vérifiez le backend.';
        this.loading = false;
      },
    });
  }
}

