############ Class Definitions ############
import random
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Callable

class QualityGenerator(ABC):
    @abstractmethod
    def generate_quality(self, description: str) -> int:
        pass
class TestQualityGenerator(QualityGenerator):
    def generate_quality(self, description: str) -> int:
        # A simple deterministic implementation for testing
        return 42  # Arbitrary test value

class DifficultyGenerator(ABC):
    @abstractmethod
    def generate_difficulty(self, description: str) -> int:
        pass

class TestDifficultyGenerator(DifficultyGenerator):
    def generate_difficulty(self, description: str) -> int:
        # A simple deterministic implementation for testing
        return 50  # Arbitrary test value
    
class SuggestionGenerator(ABC):
    @abstractmethod
    def make_suggestion(self, description: str) -> str:
        pass

class SimpleSuggestionGenerator(SuggestionGenerator):
    def make_suggestion(self, description: str) -> str:
        return description + " (updated)"
    

class Reward(ABC):
    def __init__(self, value: int, description: str):
        self.value = value
        self.description = description

    @abstractmethod
    def activate(self):
        pass

class Key(Reward):
    def __init__(self, value: int, description: str, key_name: str):
        super().__init__(value, description)
        self.key_name = key_name

    def activate(self):
        # Implementation for activating a key, if needed
        pass
### Pool and Box Classes ###
class Pool(ABC):
    def __init__(self, rewards: List[Reward]):
        self.rewards = rewards

    def __len__(self):
        return len(self.rewards)
    
    @abstractmethod
    def select_reward(self) -> Optional[Reward]:
        pass

class RandomPool(Pool):
    def select_reward(self) -> Optional[Reward]:
        
        if self.rewards:
            #generate a random index
            index = random.randint(0, len(self.rewards) - 1)
            return self.rewards[index]

    
class Box:
    def __init__(self, pool_size: int, pool: Pool):
        self.pool_size = pool_size
        self.pool = pool

    def get_reward_pool(self, modifier: int = 0) -> List[Reward]:
        reward_pool = []
        while len(reward_pool) < self.pool_size:
            reward = self.pool.select_reward()
            if reward:
                chance = random.randint(1, 1000) + modifier
                if chance >= reward.value:
                    reward_pool.append(reward)
        return reward_pool




class LootBox(Box):
    def __init__(self, name: str, key_name: str, pool_size: int, rewards: List[Reward]):
        super().__init__(pool_size, rewards)
        self.name = name
        self.key_name = key_name

    def open_box(self, key: Key) -> List[Reward]:
        if key.key_name == self.key_name:
            return self.get_reward_pool()
        else:
            return None


### Todo and Task Classes ###

class Todo:
    def __init__(self, 
                 description: str, 
                 importance: int = 1, 
                 difficulty: Optional[int] = None, 
                 quality: Optional[int] = None, 
                 due_datetime: Optional[datetime] = None,
                 quality_generator: Optional[QualityGenerator] = None,
                 difficulty_generator: Optional[DifficultyGenerator] = None,
                 modify_score_function: Optional[Callable[[int], int]] = None):
        self.description = description
        self.importance = importance
        self.difficulty = difficulty if difficulty is not None else (difficulty_generator.generate_difficulty(description) if difficulty_generator else 1)
        self.quality = quality if quality is not None else (quality_generator.generate_quality(description) if quality_generator else 0)
        self.due_datetime = due_datetime
        self.completed = False
        self.required_subtasks: List[Todo] = []
        self.optional_subtasks: List[Todo] = []
        self.modify_score_function = modify_score_function

    def add_subtask(self, subtask: 'Todo', required: bool = True):
        if required:
            self.required_subtasks.append(subtask)
        else:
            self.optional_subtasks.append(subtask)

    def mark_complete(self):
        if all(subtask.completed for subtask in self.required_subtasks):
            self.completed = True
            self._complete_subtasks()
        else:
            raise Exception("Not all required subtasks are complete")

    def _complete_subtasks(self):
        for subtask in self.required_subtasks:
            subtask.mark_complete()
        for subtask in self.optional_subtasks:
            subtask.mark_complete()

    def get_value(self):
        base_value = self.importance * self.difficulty
        if self.modify_score_function:
            return self.modify_score_function(base_value)
        return base_value

    def __str__(self):
        return (f"Todo(description={self.description}, importance={self.importance}, "
                f"difficulty={self.difficulty}, quality={self.quality}, "
                f"due_datetime={self.due_datetime}, completed={self.completed})")


class TaskCreationStrategy(ABC):
    @abstractmethod
    def create_task(self, todos: List[Todo], 
                    description: str, 
                    importance: int, 
                    difficulty_generator: DifficultyGenerator, 
                    quality_generator: QualityGenerator, 
                    suggestion_generator: SuggestionGenerator, 
                    reward_box: LootBox, 
                    punishment_box: LootBox) -> Optional[List[Reward]]:
        pass

class SimpleTaskCreationStrategy(TaskCreationStrategy):
    def create_task(self, todos: List[Todo], 
                    description: str, 
                    importance: int, 
                    difficulty_generator: DifficultyGenerator, 
                    quality_generator: QualityGenerator, 
                    suggestion_generator: SuggestionGenerator, 
                    reward_box: Box, 
                    punishment_box: Box) -> Optional[List[Reward]]:
        new_todo = Todo(description, importance=importance, difficulty_generator=difficulty_generator, quality_generator=quality_generator)
        add_todo(todos, new_todo)

        quality = new_todo.quality
        modifier = quality * (11 - importance)

        if modifier > 0:
            rewards = reward_box.get_reward_pool(modifier)
            if rewards:
                print(f"Opened reward box and received rewards:")
                reward = RandomPool(rewards).select_reward()
                print(reward.description)
                reward.activate()
                return reward
            else:
                print("Failed to open reward box.")
                return None
        else:
            random_chance = random.randint(1, 10)
            if random_chance >= importance:
                rewards = punishment_box.get_reward_pool(modifier)
                reward = RandomPool(rewards).select_reward()
                if rewards:
                    print(f"Opened punishment box and received rewards:")
                    print(reward.description)
                    reward.activate()
                    return reward
                else:
                    print("Failed to open punishment box.")
                    return None
            else:
                new_description = suggestion_generator.make_suggestion(description)
                print(f"Suggestion made: {new_description}")
                return self.create_task(todos, new_description, importance, difficulty_generator, quality_generator, suggestion_generator, reward_box, punishment_box)

######################## Helper Functions ########################
def get_todo(todos: List[Todo], description: str) -> Optional[Todo]:
    for todo in todos:
        if todo.description == description:
            return todo
    return None

def update_todo(todos: List[Todo], description: str, updates: dict) -> bool:
    todo = get_todo(todos, description)
    if todo:
        for attr, value in updates.items():
            if hasattr(todo, attr):
                setattr(todo, attr, value)
        return True
    return False

def remove_todo(todos: List[Todo], description: str) -> bool:
    todo = get_todo(todos, description)
    if todo:
        todos.remove(todo)
        return True
    return False

def add_todo(todos: List[Todo], todo: Todo) -> None:
    todos.append(todo)


### List Dos ###
def list_todos(todos: List[Todo]) -> List[Todo]:
    return todos

def list_todos_by_completion_status(todos: List[Todo], completed: bool) -> List[Todo]:
    return [todo for todo in todos if todo.completed == completed]

def list_todos_by_importance(todos: List[Todo], importance: int) -> List[Todo]:
    return [todo for todo in todos if todo.importance == importance]

def list_todos_by_due_date(todos: List[Todo], due_date: datetime) -> List[Todo]:
    return [todo for todo in todos if todo.due_datetime == due_date]


######################## Testing ########################
# Example usage
if __name__ == "__main__":
    def custom_modifier(value):
        return value + 10

    quality_generator = TestQualityGenerator()
    difficulty_generator = TestDifficultyGenerator()
    suggestion_generator = SimpleSuggestionGenerator()

    todos = []

    reward1 = Key(100, "Reward Key 1", "reward_key_1")
    reward2 = Key(200, "Reward Key 2", "reward_key_2")
    reward3 = Key(300, "Reward Key 3", "reward_key_3")

    punishment1 = Key(50, "Punishment Key 1", "punishment_key_1")
    punishment2 = Key(100, "Punishment Key 2", "punishment_key_2")
    punishment3 = Key(150, "Punishment Key 3", "punishment_key_3")

    reward_pool = RandomPool([reward1, reward2, reward3])
    punishment_pool = RandomPool([punishment1, punishment2, punishment3])

    reward_box = Box(3, reward_pool)
    punishment_box = Box(3, punishment_pool)

    task_creation_strategy = SimpleTaskCreationStrategy()
    reward = task_creation_strategy.create_task(todos, "Main task", 5, difficulty_generator, quality_generator, suggestion_generator, reward_box, punishment_box)

    print("All Todos:")
    for todo in list_todos(todos):
        print(todo)

    if reward:
        print("Reward received:")
        print(reward.description)