import from byllm.lib { Model }
import from datetime { datetime }
glob llm = Model(model_name="ollama/llama3");


obj University {
    has name: str;
    has location: str;
    has ranking: int;
}

obj Class{
    has class_name: str;
    has professor: str;
    has credits: int;
}
enum gender {
    MALE,
    FEMALE,
    OTHER
}

obj Student {
    has name: str;
    has date_of_birth: str;
    has gender : gender;
    has grade: str;
    has classes: list[Class];
    has university: University;
    def introduce() -> str by llm();
}

def generate_student(gender: gender) -> Student by llm(temperature=0.4);

def calculate_age(Student: Student) -> int by llm(incl_info={
            "today": get_date()});

def get_date() -> str {
    return datetime.now().strftime("%d-%m-%Y");
}

with entry {
    let student_m = generate_student(gender=gender.MALE);
    let age_m = calculate_age(Student=student_m);
    print("########### student introduction ############");
    print(student_m.introduce());
    print("########### student age ############");
    print(f"student age: {age_m}, studen date of birth: {student_m.date_of_birth}");
    print("########### student info ############");
    print(f"student info: {student_m}");

}