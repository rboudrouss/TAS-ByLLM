
# 3. Exemples

## `translator.jac` (par Function Definitions)

On souhaite traduire une phrase vers une langue donnée.
```python
def translate_to(language: str, phrase: str) -> str by llm()
```

Appel de la fonction:
```python
with entry {
    lang = "French";
    phrase = "Hello, how are you?";
    output = translate_to(language=lang, phrase=phrase);
    print(output);
}
```

En suivant l'algorithme MT-IR et la synthèse de prompt de MTP, le prompt généré par la sémantique du code (lors de l'appel de la fonction seulement) serait :


```js
[System Prompt]
This is an operation you must perform and return the output values.

[Inputs_Information]

(language) (str) = "French"
(phrase) (str) = "Hello, how are you?"

[Output_Information]
(str)

[Type_Explanations]
(str)

[Action]
translate_to
Generate and return the output result(s) only, adhering to the provided Type in the
following format
[Output]
<result>

```

stdin:
```
Bonjour, comment allez-vous ?
```
## `studentGenerator.jac` (par Function Definitions et Member Method Definition)

Ce programme, plus complexe, génère un étudiant et détermine son âge à partir de sa date de naissance. On a 3 objets : `Student`, `University` et `Class`, avec un enum représentant le genre.

```ts
obj University {
    has name: str;
    has location: str;
    has ranking: int;
}
```
```ts
obj Class{
    has class_name: str;
    has professor: str;
    has credits: int;
}
```
```ts
enum Gender {
    MALE,
    FEMALE,
    OTHER
}
```

```ts
obj Student {
    has name: str;
    has date_of_birth: str;
    has gender : Gender;
    has grade: str;
    has classes: list[Class];
    has university: University;
    def introduce() -> str by llm();
}
```

On remarque la méthode `Student.introduce()` qui délègue la génération du texte au modèle via `llm()`, produisant une courte présentation de l'étudiant. Le mot-clé `by` sur une méthode extrait également le contexte sémantique de son objet. On ajoute deux fonctions : `generate_student(gender: Gender)` qui génère un `Student` selon son genre, et `calculate_age(student: Student)` qui calcule l'âge de l'étudiant à partir de sa date de naissance.

```
def generate_student(gender: gender) -> Student by llm(temperature=0.4);
```
Pour que la fonction de calcul de l'âge fonctionne correctement, on peut inclure des informations supplémentaires dans `llm()`, ici la date du jour.
```
def calculate_age(Student: Student) -> int by llm(incl_info={
            "today": datetime.now()});
```

On génère un étudiant homme, on calcule son âge, et on l'introduit.
```python
    let student_m = generate_student(gender=gender.MALE);
    let age_m = calculate_age(Student=student_m);
    print("########### student introduction ############");
    print(student_m.introduce());
    print("########### student age ############");
    print(f"student age: {age_m}, studen date of birth: {student_m.date_of_birth}");
    print("########### student info ############");
    print(f"student info: {student_m}");
```


**Exemple d'output:**
```
########### student introduction ############
Student 'John Doe' born on '1990-01-01',
 male,
 in 12th grade at University of Technology (ranked 10) in New York.
########### student age ############
student age: 35, student date of birth: 1990-01-01
########### student info ############
student info: Student(name='John Doe',
                    date_of_birth='1990-01-01',
                    sex=<sex.MALE: 1>,
                    grade='12th',
                    classes=[],
                    university=University(name='University of Technology',
                    location='New York', ranking=10))
```

En suivant l'algorithme MT-IR et la synthèse de prompt de MTP, le prompt généré par la sémantique de l'appel de `generate_student` ressemblerait à :

```js
[System Prompt]
This is an operation you must perform and return the output values.

[Inputs_Information]

(gender) (Gender) = MALE

[Output_Information]
(Student)

[Type_Explanations]
(Student)(obj)eg:
- Student(name:str,gender:Gender..,classes:list[Class],university:University)
(Gender) (enum)eg:
- Gender(MALE,FEMALE,OTHER)
(Class)(obj)eg:
- Class(class_name:str,professor:str,credits:int)
(University)(obj)eg:
- University(name:str,location:str,ranking:int)

[Action]
generate_student
Generate and return the output result(s) only, adhering to the provided Type in the
following format
[Output]
<result>
```