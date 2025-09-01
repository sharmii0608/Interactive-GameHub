import tkinter as tk
from tkinter import messagebox
import chess
import time

# ---------- Display ----------
LIGHT = "#EEEED2"
DARK = "#769656"
HILITE = "#BACA44"
SIZE = 64             # square size
BOARD_PIX = SIZE * 8
FONT_FAMILY_TRY = ("Segoe UI Symbol", "Arial Unicode MS", "DejaVu Sans", "Arial")
PIECE_FONT = None     # chosen at runtime

UNICODE_PIECES = {
    'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
    'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚'
}

# ---------- Simple Evaluation ----------
PIECE_VALUES = {
    chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
    chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 20000
}

def evaluate(board: chess.Board) -> int:
    """Material-only evaluation (White positive)."""
    if board.is_checkmate():
        return -10**9 if board.turn else 10**9
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    score = 0
    for sq in chess.SQUARES:
        p = board.piece_at(sq)
        if p:
            score += PIECE_VALUES[p.piece_type] if p.color else -PIECE_VALUES[p.piece_type]
    return score

# ---------- Alpha-Beta (returns score ONLY) ----------
INF = 10**9

def search(board: chess.Board, depth: int, alpha: int, beta: int) -> int:
    """Negamax with alpha-beta pruning (returns ONLY score)."""
    if depth == 0 or board.is_game_over():
        return evaluate(board)

    best = -INF
    # Simple move ordering: try captures first
    moves = list(board.legal_moves)
    moves.sort(key=lambda m: board.is_capture(m), reverse=True)

    for mv in moves:
        board.push(mv)
        score = -search(board, depth - 1, -beta, -alpha)
        board.pop()

        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break
    return best

def choose_best_move(board: chess.Board, depth: int) -> chess.Move | None:
    """Pick the move that maximizes search score."""
    best_move = None
    best_score = -INF

    moves = list(board.legal_moves)
    moves.sort(key=lambda m: board.is_capture(m), reverse=True)

    for mv in moves:
        board.push(mv)
        score = -search(board, depth - 1, -INF, INF)
        board.pop()

        if score > best_score:
            best_score = score
            best_move = mv
    return best_move

# ---------- GUI ----------
class ChessGUI:
    def __init__(self, root):
        global PIECE_FONT
        self.root = root
        self.root.title("Chess vs AI (Unicode GUI)")
        # Pick a font that has chess glyphs
        for fam in FONT_FAMILY_TRY:
            try:
                PIECE_FONT = (fam, 36)
                break
            except Exception:
                continue
        if PIECE_FONT is None:
            PIECE_FONT = ("Arial", 36)

        self.canvas = tk.Canvas(root, width=BOARD_PIX, height=BOARD_PIX, highlightthickness=0)
        self.canvas.pack()

        self.status = tk.Label(root, text="You are White. Click a piece, then a square.")
        self.status.pack(pady=6)

        self.board = chess.Board()
        self.sel_from = None          # selected square (int) or None
        self.sel_square_rc = None     # (row, col) for highlight
        self.depth = 2                # AI depth

        self.draw_board()
        self.canvas.bind("<Button-1>", self.on_click)

    def draw_board(self):
        self.canvas.delete("all")
        # squares
        for r in range(8):
            for c in range(8):
                x1, y1 = c * SIZE, r * SIZE
                x2, y2 = x1 + SIZE, y1 + SIZE
                color = LIGHT if (r + c) % 2 == 0 else DARK
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=color)
        # highlight selected
        if self.sel_square_rc:
            r, c = self.sel_square_rc
            x1, y1 = c * SIZE, r * SIZE
            x2, y2 = x1 + SIZE, y1 + SIZE
            self.canvas.create_rectangle(x1, y1, x2, y2, outline=HILITE, width=4)

        # pieces
        for r in range(8):
            for c in range(8):
                sq = chess.square(c, 7 - r)   # convert GUI row to chess square
                p = self.board.piece_at(sq)
                if p:
                    sym = UNICODE_PIECES[p.symbol()]
                    self.canvas.create_text(
                        c * SIZE + SIZE // 2,
                        r * SIZE + SIZE // 2,
                        text=sym,
                        font=PIECE_FONT
                    )

        # rank/file labels for better understanding
        for c in range(8):
            file_char = chr(ord('a') + c)
            self.canvas.create_text(c * SIZE + 6, BOARD_PIX - 10, text=file_char, anchor="w", fill="#333")
        for r in range(8):
            rank_char = str(8 - r)
            self.canvas.create_text(4, r * SIZE + 10, text=rank_char, anchor="w", fill="#333")

    def on_click(self, event):
        col, row = event.x // SIZE, event.y // SIZE
        if not (0 <= col < 8 and 0 <= row < 8):
            return
        sq = chess.square(col, 7 - row)

        if self.sel_from is None:
            # select your own piece (side to move)
            piece = self.board.piece_at(sq)
            if piece and piece.color == self.board.turn and piece.color == chess.WHITE:
                self.sel_from = sq
                self.sel_square_rc = (row, col)
                self.draw_board()
        else:
            # attempt a move
            move = self._make_move(self.sel_from, sq)
            self.sel_from = None
            self.sel_square_rc = None
            self.draw_board()

            if move:
                self.root.after(200, self.ai_turn)

    def _make_move(self, from_sq: int, to_sq: int) -> chess.Move | None:
        """Handle promotions to queen automatically."""
        move = chess.Move(from_sq, to_sq)

        # if a simple move isn't legal, try promotion (when pawn reaches last rank)
        if move not in self.board.legal_moves:
            piece = self.board.piece_at(from_sq)
            if piece and piece.piece_type == chess.PAWN:
                to_rank = chess.square_rank(to_sq)
                if (piece.color == chess.WHITE and to_rank == 7) or (piece.color == chess.BLACK and to_rank == 0):
                    move = chess.Move(from_sq, to_sq, promotion=chess.QUEEN)

        if move in self.board.legal_moves:
            self.board.push(move)
            self.status.config(text=f"You played: {move.uci()}")
            self._check_game_over()
            return move
        else:
            self.status.config(text="Illegal move. Try again.")
            return None

    def ai_turn(self):
        if self.board.is_game_over():
            return
        self.status.config(text="AI thinking...")
        self.root.update()
        start = time.time()
        mv = choose_best_move(self.board, self.depth)
        if mv is not None:
            # auto-promote if needed
            if (self.board.piece_at(mv.from_square) and
                self.board.piece_at(mv.from_square).piece_type == chess.PAWN):
                to_rank = chess.square_rank(mv.to_square)
                if (self.board.turn == chess.BLACK and to_rank == 0) or (self.board.turn == chess.WHITE and to_rank == 7):
                    mv = chess.Move(mv.from_square, mv.to_square, promotion=chess.QUEEN)

            self.board.push(mv)
            elapsed = time.time() - start
            self.status.config(text=f"AI moved: {mv.uci()}  (in {elapsed:.2f}s)")
            self.draw_board()
            self._check_game_over()
        else:
            self.status.config(text="AI has no legal moves.")

    def _check_game_over(self):
        if self.board.is_game_over():
            res = self.board.result()
            if self.board.is_checkmate():
                msg = "Checkmate!"
            elif self.board.is_stalemate():
                msg = "Stalemate!"
            else:
                msg = "Game over."
            messagebox.showinfo("Result", f"{msg} Result: {res}")
            self.status.config(text=f"{msg} Result: {res}")

def main():
    root = tk.Tk()
    app = ChessGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
