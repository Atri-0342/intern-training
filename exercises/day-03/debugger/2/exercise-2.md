Install rr and use reverse debugging to find a corruption bug. Save this program as corruption.c:
class Student:
    def __init__(self, student_id, scores):
        self.id = student_id
        self.scores = scores


students = [
    Student(1001, [85, 92, 78]),
    Student(1002, [90, 88, 95])
]


def init():
    pass


def curve_scores(student_idx, curve):
    for i in range(3):
        students[student_idx].scores[i] += curve


def main():
    print("=== Initial state ===")
    print(f"Student 0: id={students[0].id}")
    print(f"Student 1: id={students[1].id}")

    curve_scores(0, 5)

    print("\n=== After curving ===")
    print(f"Student 0: id={students[0].id}")
    print(f"Student 1: id={students[1].id}")

    if students[1].id != 1002:
        print(
            f"\nERROR: Student 1's ID was corrupted! "
            f"Expected 1002, got {students[1].id}"
        )
        return 1

    return 0


if __name__ == "__main__":
    main()
    
#include <stdio.h>

typedef struct {
    int id;
    int scores[3];
} Student;

Student students[2];

void init() {
    students[0].id = 1001;
    students[0].scores[0] = 85;
    students[0].scores[1] = 92;
    students[0].scores[2] = 78;

    students[1].id = 1002;
    students[1].scores[0] = 90;
    students[1].scores[1] = 88;
    students[1].scores[2] = 95;
}

void curve_scores(int student_idx, int curve) {
    for (int i = 0; i < 4; i++) {
        students[student_idx].scores[i] += curve;
    }
}

int main() {
    init();
    printf("=== Initial state ===\n");
    printf("Student 0: id=%d\n", students[0].id);
    printf("Student 1: id=%d\n", students[1].id);

    curve_scores(0, 5);

    printf("\n=== After curving ===\n");
    printf("Student 0: id=%d\n", students[0].id);
    printf("Student 1: id=%d\n", students[1].id);

    if (students[1].id != 1002) {
        printf("\nERROR: Student 1's ID was corrupted! Expected 1002, got %d\n",
               students[1].id);
        return 1;
    }
    return 0;
}
Compile with gcc -g corruption.c -o corruption and run it. Student 1’s ID gets corrupted, but the corruption happens in a function that only touches student 0. Use rr record ./corruption and rr replay to find the culprit. Set a watchpoint on students[1].id and use reverse-continue after the corruption to find exactly which line of code overwrote it.

