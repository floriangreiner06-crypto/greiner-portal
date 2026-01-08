# /commit - Git Commit erstellen

Erstelle einen strukturierten Git Commit.

## Anweisungen

1. **Prüfe Status:**
   ```
   git status
   git diff --stat
   ```

2. **Analysiere Änderungen:**
   - Welche Dateien wurden geändert
   - Was ist der Hauptzweck der Änderungen

3. **Commit-Message Format:**
   ```
   <type>(TAG[X]): <Kurzbeschreibung>

   - Detail 1
   - Detail 2

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
   ```

4. **Types:**
   - `feat` - Neues Feature
   - `fix` - Bugfix
   - `docs` - Dokumentation
   - `refactor` - Code-Refactoring
   - `style` - Formatting
   - `chore` - Maintenance

5. **Frage den User:**
   - Welche Dateien sollen committed werden
   - Bestätigung der Commit-Message

## Nach dem Commit
Frage ob Push gewünscht ist.
