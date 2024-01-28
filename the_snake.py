import random

import pygame

# Инициализация PyGame:
pygame.init()

# Константы для размеров поля и сетки:
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE
# Направления движения:
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# Цвет фона - черный:
BOARD_BACKGROUND_COLOR = (0, 0, 0)

# Цвет границы ячейки:
BORDER_COLOR = (93, 216, 228)

# Цвет яблока:
APPLE_COLOR = (255, 0, 0)

# Цвет змейки:
SNAKE_COLOR = (0, 255, 0)

# Скорость движения змейки:
SPEED = 10

# Настройка игрового окна:
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)

# Заголовок окна игрового поля:
pygame.display.set_caption("Змейка")

# Настройка времени:
clock = pygame.time.Clock()


class GameObject:
    """Базовый класс для игровых объектов."""

    def __init__(self, bg_color=None):
        """Инициализация игрового объекта."""
        self.body_color = bg_color
        self.position = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    def draw(self, surface):
        """Отрисовка объекта."""
        pass


class Apple(GameObject):
    """Класс представления яблока."""

    def __init__(self, bg_color=APPLE_COLOR):
        """Инициализация яблока."""
        super().__init__(bg_color)
        self.randomize_position([])

    def randomize_position(self, snake_positions):
        """Установка случайного положения яблока."""
        while True:
            new_position = (
                random.randint(1, GRID_WIDTH - 2) * GRID_SIZE,
                random.randint(1, GRID_HEIGHT - 2) * GRID_SIZE,
            )
            if new_position not in snake_positions:
                self.position = new_position
                break

    def draw(self, surface):
        """Отрисовка яблока."""
        rect = pygame.Rect(
            (self.position[0], self.position[1]),
            (GRID_SIZE, GRID_SIZE)
        )
        pygame.draw.rect(surface, self.body_color, rect)
        pygame.draw.rect(surface, BORDER_COLOR, rect, 1)


class Snake(GameObject):
    """Класс представления змейки."""

    def __init__(self, bg_color=SNAKE_COLOR):
        """Инициализация змейки."""
        super().__init__(bg_color)
        self.length = 1
        self.direction = RIGHT
        self.next_direction = None
        self.body_color = bg_color
        self.positions = [(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)]

    def update_direction(self, event):
        """Обновление направления движения змейки по нажатию клавиши."""
        if event.key == pygame.K_UP and self.direction != DOWN:
            self.next_direction = UP
        elif event.key == pygame.K_DOWN and self.direction != UP:
            self.next_direction = DOWN
        elif event.key == pygame.K_LEFT and self.direction != RIGHT:
            self.next_direction = LEFT
        elif event.key == pygame.K_RIGHT and self.direction != LEFT:
            self.next_direction = RIGHT

    def move(self):
        """Перемещение змейки."""
        x, y = self.direction
        head_x, head_y = self.get_head_position()
        new_head_x = (head_x + x) % SCREEN_WIDTH
        new_head_y = (head_y + y) % SCREEN_HEIGHT
        new_head = (new_head_x, new_head_y)
        self.positions.insert(0, new_head)
        if len(self.positions) > self.length:
            self.positions.pop()

        if self.next_direction:
            self.direction = self.next_direction
            self.next_direction = None

    def draw(self, surface):
        """Отрисовка змейки."""
        for position in self.positions:
            rect = pygame.Rect(
                (position[0], position[1]),
                (GRID_SIZE, GRID_SIZE)
            )
            pygame.draw.rect(surface, self.body_color, rect)
            pygame.draw.rect(surface, BORDER_COLOR, rect, 1)

    def get_head_position(self):
        """Возвращает голову змейки."""
        return self.positions[0]

    def self_collision(self):
        """Возвращает True, если змейка сталкивается с собой."""
        head_position = self.get_head_position()
        for position in self.positions[1:]:
            if position == head_position:
                return True
        return False

    def reset(self):
        """
        Сбрасывает змейку в начальное состояние
        после столкновения с собой.
        """
        self.length = 1
        self.direction = RIGHT
        self.next_direction = None
        self.positions = [(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)]


def handle_keys(snake):
    """Обработчик нажатия клавиш."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        elif event.type == pygame.KEYDOWN:
            snake.update_direction(event)
    return True


def main():
    """
    Функция main инициализирует экземпляры классов
    Snake и Apple и управляет игровым циклом.
    """
    # Создаем экземпляры классов:
    snake = Snake()
    apple = Apple()

    running = True
    while running:
        running = handle_keys(snake)

        snake.move()

        if snake.get_head_position() == apple.position:
            snake.length += 1
            apple.randomize_position(snake.positions)

        if snake.self_collision():
            snake.reset()

        screen.fill(BOARD_BACKGROUND_COLOR)
        snake.draw(screen)
        apple.draw(screen)
        pygame.display.update()
        clock.tick(SPEED)

    pygame.quit()


if __name__ == "__main__":
    main()
