from rich.progress import BarColumn, Progress, TimeElapsedColumn


class ProgressBar:
    OPTIONS = [
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.completed:>6}/{task.total}",
        TimeElapsedColumn(),
    ]

    def __init__(self, description, total):
        self.description = description
        self.total = total

    def __enter__(self):
        self.progress = Progress(*self.OPTIONS)
        self.progress.start()
        self.task = self.progress.add_task(self.description, total=self.total)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.progress.stop()

    def print(self, message):
        self.progress.console.print(message)

    def advance(self, advance=1):
        self.progress.update(self.task, advance=advance)
