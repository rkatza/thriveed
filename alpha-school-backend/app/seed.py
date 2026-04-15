import json
from app.database import get_db
from app.auth import hash_password

def seed_database():
    with get_db() as db:
        # Check if already seeded
        existing = db.execute("SELECT COUNT(*) as c FROM users").fetchone()
        if existing["c"] > 0:
            return

        # Create school
        db.execute("INSERT INTO schools (name, address, city, phone) VALUES (?, ?, ?, ?)",
                   ("Colegio ThriveEd Panama", "Calle 50, Bella Vista", "Ciudad de Panama", "+507-300-1234"))

        # Create grades
        db.execute("INSERT INTO grades (school_id, name, level) VALUES (1, '4to Grado', 4)")
        db.execute("INSERT INTO grades (school_id, name, level) VALUES (1, 'Kinder', 0)")

        # Create classrooms
        db.execute("INSERT INTO classrooms (grade_id, name, group_type) VALUES (1, 'Salon 4-A', 'treatment')")
        db.execute("INSERT INTO classrooms (grade_id, name, group_type) VALUES (1, 'Salon 4-B', 'control')")
        db.execute("INSERT INTO classrooms (grade_id, name, group_type) VALUES (2, 'Salon Kinder-A', 'treatment')")

        # Create users - Admin (user_id=1)
        db.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
                   ("admin@thriveed.edu.pa", hash_password("admin123"), "super_admin", "Director", "Pedagogico"))

        # Create users - Coaches (user_id=2,3)
        db.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
                   ("coach1@thriveed.edu.pa", hash_password("coach123"), "coach", "Maria", "Gonzalez"))
        db.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
                   ("coach2@thriveed.edu.pa", hash_password("coach123"), "coach", "Carlos", "Rodriguez"))

        # Create coach records
        db.execute("INSERT INTO coaches (user_id, classroom_id, specialization) VALUES (2, 1, 'Matematicas')")
        db.execute("INSERT INTO coaches (user_id, classroom_id, specialization) VALUES (3, 2, 'Matematicas')")

        # Create students - 4to Grado (user_id 4-10, student_id 1-7)
        student_data_4to = [
            ("sofia@thriveed.edu.pa", "Sofia", "Martinez", 9, '["deportes","musica","animales"]'),
            ("diego@thriveed.edu.pa", "Diego", "Lopez", 10, '["videojuegos","dinosaurios","espacio"]'),
            ("valentina@thriveed.edu.pa", "Valentina", "Perez", 9, '["arte","cocina","naturaleza"]'),
            ("camila@thriveed.edu.pa", "Camila", "Hernandez", 9, '["musica","arte","animales"]'),
            ("santiago@thriveed.edu.pa", "Santiago", "Diaz", 10, '["espacio","dinosaurios","naturaleza"]'),
            ("isabella@thriveed.edu.pa", "Isabella", "Torres", 9, '["cocina","deportes","musica"]'),
            ("sebastian@thriveed.edu.pa", "Sebastian", "Ramirez", 10, '["videojuegos","carros","deportes"]'),
        ]

        avatars_4to = ['A', 'B', 'C', 'D', 'E', 'F', 'G']

        for i, (email, first, last, age, interests) in enumerate(student_data_4to):
            uid = i + 4  # user_id starts at 4
            db.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
                       (email, hash_password("student123"), "student", first, last))
            classroom_id = 1 if i < 5 else 2
            db.execute("INSERT INTO students (user_id, classroom_id, nickname, avatar_url, age, interests) VALUES (?, ?, ?, ?, ?, ?)",
                       (uid, classroom_id, first, avatars_4to[i], age, interests))

        # Create students - Kinder (user_id 11-13, student_id 8-10)
        student_data_kinder = [
            ("mateo@thriveed.edu.pa", "Mateo", "Garcia", 5, '["animales","colores","musica"]'),
            ("lucia@thriveed.edu.pa", "Lucia", "Vargas", 5, '["princesas","colores","cocina"]'),
            ("emilio@thriveed.edu.pa", "Emilio", "Castillo", 6, '["dinosaurios","carros","animales"]'),
        ]

        avatars_kinder = ['H', 'I', 'J']

        for i, (email, first, last, age, interests) in enumerate(student_data_kinder):
            uid = len(student_data_4to) + 4 + i
            db.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
                       (email, hash_password("student123"), "student", first, last))
            db.execute("INSERT INTO students (user_id, classroom_id, nickname, avatar_url, age, interests) VALUES (?, ?, ?, ?, ?, ?)",
                       (uid, 3, first, avatars_kinder[i], age, interests))

        # Create parents (user_id 14-17, parent_id 1-4)
        parent_data = [
            ("padre.martinez@gmail.com", "Roberto", "Martinez", "+507-6000-1001"),
            ("madre.lopez@gmail.com", "Ana", "Lopez", "+507-6000-1002"),
            ("padre.perez@gmail.com", "Juan", "Perez", "+507-6000-1003"),
            ("madre.garcia@gmail.com", "Laura", "Garcia", "+507-6000-1004"),
        ]

        for i, (email, first, last, phone) in enumerate(parent_data):
            uid = len(student_data_4to) + len(student_data_kinder) + 4 + i
            db.execute("INSERT INTO users (email, password_hash, role, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
                       (email, hash_password("parent123"), "parent", first, last))
            db.execute("INSERT INTO parents (user_id, phone) VALUES (?, ?)", (uid, phone))

        # Link parents to students
        db.execute("INSERT INTO parent_students (parent_id, student_id) VALUES (1, 1)")  # Roberto -> Sofia
        db.execute("INSERT INTO parent_students (parent_id, student_id) VALUES (2, 2)")  # Ana -> Diego
        db.execute("INSERT INTO parent_students (parent_id, student_id) VALUES (3, 3)")  # Juan -> Valentina
        db.execute("INSERT INTO parent_students (parent_id, student_id) VALUES (4, 8)")  # Laura -> Mateo

        # ===========================================
        # MATH SKILLS TREE - 4th Grade Panama
        # ===========================================
        skills_data_4to = [
            (1, "Lectura de numeros hasta 10,000", "Leer y escribir numeros naturales hasta 10,000", "numeros", 1, None, 1),
            (2, "Valor posicional", "Identificar unidades, decenas, centenas y millares", "numeros", 1, 1, 2),
            (3, "Comparacion de numeros", "Comparar numeros usando >, < e =", "numeros", 2, 2, 3),
            (4, "Ordenar numeros", "Ordenar numeros de menor a mayor y viceversa", "numeros", 2, 3, 4),
            (5, "Redondeo", "Redondear numeros a la decena y centena mas cercana", "numeros", 3, 4, 5),
            (6, "Suma basica", "Sumar numeros de un digito", "operaciones", 1, None, 6),
            (7, "Suma con reagrupacion", "Sumar numeros de dos digitos con reagrupacion", "operaciones", 2, 6, 7),
            (8, "Suma de tres digitos", "Sumar numeros de tres digitos", "operaciones", 2, 7, 8),
            (9, "Suma de cuatro digitos", "Sumar numeros de hasta cuatro digitos", "operaciones", 3, 8, 9),
            (10, "Propiedades de la suma", "Conmutativa, asociativa, elemento neutro", "operaciones", 3, 9, 10),
            (11, "Resta basica", "Restar numeros de un digito", "operaciones", 1, None, 11),
            (12, "Resta con reagrupacion", "Restar con prestamo", "operaciones", 2, 11, 12),
            (13, "Resta de tres digitos", "Restar numeros de tres digitos", "operaciones", 2, 12, 13),
            (14, "Resta de cuatro digitos", "Restar numeros de hasta cuatro digitos", "operaciones", 3, 13, 14),
            (15, "Tablas del 1-5", "Multiplicacion basica tablas 1 a 5", "multiplicacion", 1, None, 15),
            (16, "Tablas del 6-9", "Multiplicacion tablas 6 a 9", "multiplicacion", 2, 15, 16),
            (17, "Multiplicacion por 10, 100", "Multiplicar por potencias de 10", "multiplicacion", 2, 16, 17),
            (18, "Multiplicacion de dos digitos", "Multiplicar numeros de dos digitos", "multiplicacion", 3, 17, 18),
            (19, "Propiedades de la multiplicacion", "Conmutativa, asociativa, distributiva", "multiplicacion", 3, 18, 19),
            (20, "Division basica", "Dividir numeros simples", "division", 1, 15, 20),
            (21, "Division con residuo", "Division con residuo", "division", 2, 20, 21),
            (22, "Division de dos digitos", "Dividir entre divisores de dos digitos", "division", 3, 21, 22),
            (23, "Concepto de fraccion", "Entender numerador y denominador", "fracciones", 1, None, 23),
            (24, "Fracciones equivalentes", "Identificar fracciones equivalentes", "fracciones", 2, 23, 24),
            (25, "Comparar fracciones", "Comparar fracciones con mismo denominador", "fracciones", 2, 24, 25),
            (26, "Suma de fracciones", "Sumar fracciones con mismo denominador", "fracciones", 3, 25, 26),
            (27, "Figuras geometricas", "Identificar triangulos, cuadrados, rectangulos, circulos", "geometria", 1, None, 27),
            (28, "Perimetro", "Calcular el perimetro de figuras simples", "geometria", 2, 27, 28),
            (29, "Area", "Calcular el area de rectangulos y cuadrados", "geometria", 3, 28, 29),
            (30, "Problemas de suma y resta", "Resolver problemas verbales con suma y resta", "problemas", 2, 8, 30),
            (31, "Problemas de multiplicacion", "Resolver problemas verbales con multiplicacion", "problemas", 3, 18, 31),
            (32, "Problemas multi-paso", "Resolver problemas que requieren mas de una operacion", "problemas", 4, 31, 32),
        ]

        for s in skills_data_4to:
            db.execute("INSERT INTO skills (id, name, description, category, difficulty_level, prerequisite_skill_id, order_index, curriculum_level) VALUES (?, ?, ?, ?, ?, ?, ?, '4to_grado')", s)

        # ===========================================
        # MATH SKILLS TREE - Kindergarten
        # ===========================================
        skills_data_kinder = [
            (101, "Contar del 1 al 5", "Contar objetos del 1 al 5", "conteo", 1, None, 1),
            (102, "Contar del 1 al 10", "Contar objetos del 1 al 10", "conteo", 1, 101, 2),
            (103, "Contar del 1 al 20", "Contar objetos del 1 al 20", "conteo", 2, 102, 3),
            (104, "Contar hacia atras", "Contar del 10 al 1 hacia atras", "conteo", 2, 103, 4),
            (105, "Reconocer numeros 1-5", "Identificar numeros escritos del 1 al 5", "numeros_kinder", 1, None, 5),
            (106, "Reconocer numeros 6-10", "Identificar numeros escritos del 6 al 10", "numeros_kinder", 1, 105, 6),
            (107, "Escribir numeros 1-10", "Trazar y escribir numeros del 1 al 10", "numeros_kinder", 2, 106, 7),
            (108, "Mas y menos", "Comparar grupos: cual tiene mas, cual tiene menos", "comparacion", 1, None, 8),
            (109, "Grande y pequeno", "Comparar objetos por tamano", "comparacion", 1, 108, 9),
            (110, "Ordenar por tamano", "Ordenar 3 objetos de menor a mayor", "comparacion", 2, 109, 10),
            (111, "Sumar con los dedos hasta 5", "Sumar usando los dedos, resultados hasta 5", "suma_kinder", 1, 101, 11),
            (112, "Sumar hasta 10", "Sumar dos numeros con resultado hasta 10", "suma_kinder", 2, 111, 12),
            (113, "Historias de suma", "Resolver problemas simples de agregar", "suma_kinder", 2, 112, 13),
            (114, "Quitar objetos hasta 5", "Restar quitando objetos, hasta 5", "resta_kinder", 1, 111, 14),
            (115, "Restar hasta 10", "Restar dos numeros hasta 10", "resta_kinder", 2, 114, 15),
            (116, "Circulos y cuadrados", "Identificar circulos y cuadrados", "figuras_kinder", 1, None, 16),
            (117, "Triangulos y rectangulos", "Identificar triangulos y rectangulos", "figuras_kinder", 1, 116, 17),
            (118, "Figuras en la vida real", "Reconocer figuras en objetos reales", "figuras_kinder", 2, 117, 18),
            (119, "Patrones de colores", "Identificar y continuar patrones de colores", "patrones", 1, None, 19),
            (120, "Patrones de figuras", "Identificar y continuar patrones de figuras", "patrones", 2, 119, 20),
        ]

        for s in skills_data_kinder:
            db.execute("INSERT INTO skills (id, name, description, category, difficulty_level, prerequisite_skill_id, order_index, curriculum_level) VALUES (?, ?, ?, ?, ?, ?, ?, 'kinder')", s)

        # ===========================================
        # PLACEMENT TEST QUESTIONS - 4to Grado
        # ===========================================
        placement_questions_4to = [
            (1, "Cual es el numero tres mil cuatrocientos veinticinco?", "multiple_choice",
             '["3,425","3,245","3,524","3,452"]', "3,425", "Piensa en cada palabra: tres mil = 3000, cuatrocientos = 400, veinticinco = 25",
             "Tres mil = 3,000 + cuatrocientos = 400 + veinticinco = 25 = 3,425", 1, '["general"]'),
            (2, "En el numero 5,738, que digito esta en la posicion de las centenas?", "multiple_choice",
             '["5","7","3","8"]', "7", "Las centenas son el tercer digito de derecha a izquierda",
             "En 5,738: 8=unidades, 3=decenas, 7=centenas, 5=millares", 1, '["general"]'),
            (3, "Cual es mayor: 4,589 o 4,598?", "multiple_choice",
             '["4,589","4,598","Son iguales","No se puede saber"]', "4,598",
             "Compara digito por digito de izquierda a derecha", "Los millares y centenas son iguales. En las decenas: 9 > 8, asi que 4,598 > 4,589", 2, '["general"]'),
            (6, "Cuanto es 47 + 35?", "numeric", '[]', "82",
             "Suma primero las unidades: 7+5=12, lleva 1", "47 + 35 = 82", 1, '["general"]'),
            (7, "En un partido de futbol, el equipo anoto 156 goles en la primera temporada y 287 en la segunda. Cuantos goles anotaron en total?", "numeric", '[]', "443",
             "Suma 156 + 287 paso a paso", "156 + 287 = 443 goles en total", 2, '["deportes"]'),
            (8, "Una tienda vendio 1,245 empanadas el lunes y 2,876 el martes. Cuantas empanadas vendio en total?", "numeric", '[]', "4121",
             "Suma digito por digito empezando por las unidades", "1,245 + 2,876 = 4,121", 3, '["cocina"]'),
            (11, "Cuanto es 83 - 47?", "numeric", '[]', "36",
             "Necesitas pedir prestado: 13-7=6, 7-4=3", "83 - 47 = 36", 1, '["general"]'),
            (12, "Un dinosaurio pesaba 5,400 kg y otro pesaba 2,750 kg. Cual es la diferencia de peso?", "numeric", '[]', "2650",
             "Resta 5,400 - 2,750", "5,400 - 2,750 = 2,650 kg de diferencia", 2, '["dinosaurios"]'),
            (15, "Cuanto es 7 x 4?", "numeric", '[]', "28",
             "Piensa: 7 grupos de 4, o 4 grupos de 7", "7 x 4 = 28", 1, '["general"]'),
            (16, "Cuanto es 8 x 9?", "numeric", '[]', "72",
             "Piensa: 8 x 9 es igual a 8 x 10 - 8", "8 x 9 = 72", 2, '["general"]'),
            (17, "En un estacionamiento hay 15 filas de carros con 12 carros cada una. Cuantos carros hay en total?", "numeric", '[]', "180",
             "Multiplica 15 x 12", "15 x 12 = 180 carros", 3, '["carros"]'),
            (20, "Si tienes 56 stickers y los repartes entre 8 amigos, cuantos le tocan a cada uno?", "numeric", '[]', "7",
             "Divide: 56 / 8", "56 / 8 = 7 stickers para cada amigo", 2, '["general"]'),
            (21, "Cuanto es 75 / 4?", "multiple_choice",
             '["18 residuo 3","19 residuo 1","18 residuo 1","19 residuo 3"]', "18 residuo 3",
             "4 x 18 = 72, y 75 - 72 = 3", "75 / 4 = 18 con residuo 3", 2, '["general"]'),
            (23, "Si una pizza tiene 8 rebanadas y te comes 3, que fraccion te comiste?", "multiple_choice",
             '["3/8","5/8","3/5","8/3"]', "3/8",
             "El denominador es el total de rebanadas, el numerador es lo que comiste",
             "Comiste 3 de 8 rebanadas = 3/8", 1, '["cocina"]'),
            (25, "Cual es mayor: 3/7 o 5/7?", "multiple_choice",
             '["3/7","5/7","Son iguales","No se puede comparar"]', "5/7",
             "Cuando el denominador es igual, compara los numeradores", "5/7 > 3/7 porque 5 > 3", 2, '["general"]'),
            (26, "Cuanto es 2/9 + 4/9?", "multiple_choice",
             '["6/18","6/9","2/3","6/9 = 2/3"]', "6/9",
             "Cuando los denominadores son iguales, suma los numeradores", "2/9 + 4/9 = 6/9", 3, '["general"]'),
            (27, "Cuantos lados tiene un triangulo?", "numeric", '[]', "3",
             "Tri = tres", "Un triangulo tiene 3 lados", 1, '["general"]'),
            (28, "Un campo de futbol mide 100 metros de largo y 60 metros de ancho. Cual es su perimetro?", "numeric", '[]', "320",
             "El perimetro es la suma de todos los lados", "P = 2 x (100 + 60) = 2 x 160 = 320 metros", 2, '["deportes"]'),
            (29, "Cual es el area de un rectangulo de 12 cm de largo y 5 cm de ancho?", "numeric", '[]', "60",
             "Area = largo x ancho", "A = 12 x 5 = 60 cm2", 3, '["general"]'),
            (30, "Maria tiene 345 balboas y gasta 128 en un libro. Luego recibe 75 de regalo. Cuantos balboas tiene ahora?", "numeric", '[]', "292",
             "Primero resta lo que gasto, luego suma lo que recibio", "345 - 128 = 217, luego 217 + 75 = 292 balboas", 3, '["general"]'),
        ]

        for q in placement_questions_4to:
            db.execute("""INSERT INTO questions (skill_id, question_text, question_type, options, correct_answer, hint, explanation, difficulty, is_placement, interest_tags) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)""", q)

        # ===========================================
        # PLACEMENT TEST QUESTIONS - Kindergarten
        # ===========================================
        placement_questions_kinder = [
            (101, "Cuantas manzanas hay? (imagen: 3 manzanas)", "multiple_choice",
             '["1","2","3","4"]', "3", "Cuenta cada manzana con tu dedo",
             "Hay 3 manzanas", 1, '["general"]'),
            (102, "Cuantos dedos hay en una mano?", "multiple_choice",
             '["3","4","5","10"]', "5", "Mira tu mano y cuenta",
             "Una mano tiene 5 dedos", 1, '["general"]'),
            (103, "Que numero viene despues del 7?", "multiple_choice",
             '["6","8","9","10"]', "8", "Cuenta: 6, 7, ...",
             "Despues del 7 viene el 8", 1, '["general"]'),
            (105, "Cual es el numero 4?", "multiple_choice",
             '["2","3","4","5"]', "4", "Busca el numero que se parece a una silla",
             "El numero 4", 1, '["general"]'),
            (108, "Donde hay MAS pelotas? Grupo A tiene 2, Grupo B tiene 5", "multiple_choice",
             '["Grupo A","Grupo B","Son iguales","No se sabe"]', "Grupo B", "Cuenta las pelotas de cada grupo",
             "Grupo B tiene 5 y es mas que 2", 1, '["deportes"]'),
            (111, "Si tienes 2 galletas y te dan 1 mas, cuantas tienes?", "multiple_choice",
             '["1","2","3","4"]', "3", "Junta las galletas y cuenta",
             "2 + 1 = 3 galletas", 1, '["cocina"]'),
            (112, "Cuanto es 3 + 2?", "multiple_choice",
             '["4","5","6","7"]', "5", "Usa tus dedos para contar",
             "3 + 2 = 5", 1, '["general"]'),
            (114, "Tienes 4 globos y se revienta 1. Cuantos te quedan?", "multiple_choice",
             '["1","2","3","4"]', "3", "Si quitas uno, quedan menos",
             "4 - 1 = 3 globos", 1, '["general"]'),
            (116, "Cual de estas figuras es un circulo?", "multiple_choice",
             '["Cuadrado","Triangulo","Circulo","Rectangulo"]', "Circulo",
             "Un circulo es redondo como una pelota",
             "El circulo es la figura redonda", 1, '["general"]'),
            (117, "Cuantos lados tiene un cuadrado?", "multiple_choice",
             '["2","3","4","5"]', "4", "Cuenta los lados del cuadrado",
             "Un cuadrado tiene 4 lados iguales", 1, '["general"]'),
            (119, "Si el patron es: rojo, azul, rojo, azul, ... que color sigue?", "multiple_choice",
             '["rojo","azul","verde","amarillo"]', "rojo",
             "Mira el patron: se repite rojo, azul",
             "El patron se repite: rojo, azul, rojo", 1, '["colores"]'),
        ]

        for q in placement_questions_kinder:
            db.execute("""INSERT INTO questions (skill_id, question_text, question_type, options, correct_answer, hint, explanation, difficulty, is_placement, interest_tags) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)""", q)

        # ===========================================
        # EXERCISE QUESTIONS - 4to Grado (Skills 1-5)
        # ===========================================
        exercise_questions_skills_1_5 = [
            # Skill 1: Lectura de numeros hasta 10,000
            (1, "Como se escribe el numero dos mil quinientos?", "multiple_choice",
             '["2,500","2,050","2,005","250"]', "2,500", "Dos mil = 2000, quinientos = 500", "2,500", 1, '["general"]'),
            (1, "Cual de estos numeros es ocho mil trescientos doce?", "multiple_choice",
             '["8,312","8,132","8,321","3,812"]', "8,312", "Ocho mil=8000, trescientos=300, doce=12", "8,312", 1, '["general"]'),
            (1, "Como se lee el numero 4,670?", "multiple_choice",
             '["Cuatro mil seiscientos setenta","Cuatro mil sesenta y siete","Cuarenta y seis mil setenta","Cuatro mil setecientos sesenta"]',
             "Cuatro mil seiscientos setenta", "4000+600+70", "Cuatro mil seiscientos setenta", 1, '["general"]'),
            (1, "Que numero es mil novecientos noventa y nueve?", "numeric", '[]', "1999",
             "Mil=1000, novecientos=900, noventa=90, nueve=9", "1,999", 1, '["general"]'),
            (1, "Como se escribe seis mil cuatrocientos?", "numeric", '[]', "6400",
             "Seis mil=6000, cuatrocientos=400", "6,400", 1, '["general"]'),
            (1, "Cual numero es mayor: 3,210 o 3,120?", "multiple_choice",
             '["3,210","3,120","Son iguales","No se puede saber"]', "3,210",
             "Compara digito por digito", "3,210 > 3,120", 1, '["general"]'),
            (1, "Como se lee 7,005?", "multiple_choice",
             '["Siete mil cinco","Setecientos cinco","Siete mil cincuenta","Siete mil quinientos"]',
             "Siete mil cinco", "7000+5", "Siete mil cinco", 2, '["general"]'),
            (1, "Escribe en numeros: nueve mil ciento cuarenta y tres", "numeric", '[]', "9143",
             "9000+100+40+3", "9,143", 2, '["general"]'),
            (1, "Que numero es cinco mil ochocientos sesenta?", "numeric", '[]', "5860",
             "5000+800+60", "5,860", 2, '["general"]'),
            (1, "Como se escribe tres mil setecientos veintiuno?", "numeric", '[]', "3721",
             "3000+700+20+1", "3,721", 2, '["general"]'),
            # Skill 2: Valor posicional
            (2, "En el numero 4,529, que digito esta en las unidades?", "multiple_choice",
             '["4","5","2","9"]', "9", "Las unidades son el ultimo digito", "9 esta en las unidades", 1, '["general"]'),
            (2, "En 3,847, que digito esta en las decenas?", "multiple_choice",
             '["3","8","4","7"]', "4", "Las decenas son el segundo digito de derecha a izquierda", "4 esta en las decenas", 1, '["general"]'),
            (2, "En 6,215, que digito esta en los millares?", "multiple_choice",
             '["6","2","1","5"]', "6", "Los millares son el primer digito", "6 esta en los millares", 1, '["general"]'),
            (2, "Cual es el valor del 3 en el numero 2,345?", "multiple_choice",
             '["3","30","300","3000"]', "300", "El 3 esta en la posicion de las centenas", "3 centenas = 300", 2, '["general"]'),
            (2, "Cual es el valor del 7 en el numero 7,102?", "multiple_choice",
             '["7","70","700","7000"]', "7000", "El 7 esta en la posicion de los millares", "7 millares = 7,000", 2, '["general"]'),
            (2, "En el numero 8,463, cual digito tiene el mayor valor?", "multiple_choice",
             '["8","4","6","3"]', "8", "El digito en la posicion mas alta tiene el mayor valor", "8 millares = 8,000", 2, '["general"]'),
            (2, "Que numero se forma con 5 millares, 3 centenas, 2 decenas y 7 unidades?", "numeric", '[]', "5327",
             "5000+300+20+7", "5,327", 2, '["general"]'),
            (2, "Descompone 4,896: cuantas centenas hay?", "numeric", '[]', "8",
             "En 4,896 el digito de las centenas es 8", "8 centenas", 1, '["general"]'),
            (2, "Si cambias el digito de las decenas en 1,234 por un 7, que numero obtienes?", "numeric", '[]', "1274",
             "Cambia el 3 (decenas) por 7", "1,274", 3, '["general"]'),
            (2, "En 9,081, cuantas decenas hay?", "numeric", '[]', "8",
             "El digito de las decenas es 8", "8 decenas", 1, '["general"]'),
            # Skill 3: Comparacion de numeros
            (3, "Cual simbolo va entre 2,345 __ 2,435?", "multiple_choice",
             '["<",">","=","No se sabe"]', "<", "Compara digito por digito", "2,345 < 2,435", 1, '["general"]'),
            (3, "Cual es mayor: 5,678 o 5,687?", "multiple_choice",
             '["5,678","5,687","Son iguales","No se sabe"]', "5,687",
             "Compara las decenas: 8 vs 7", "5,687 > 5,678", 1, '["general"]'),
            (3, "Ordena de menor a mayor: 1,200 y 1,020", "multiple_choice",
             '["1,020 < 1,200","1,200 < 1,020","Son iguales","1,020 = 1,200"]', "1,020 < 1,200",
             "Compara los digitos", "1,020 < 1,200", 1, '["general"]'),
            (3, "7,999 __ 8,000. Que simbolo va?", "multiple_choice",
             '["<",">","=","No se sabe"]', "<", "7 mil es menos que 8 mil", "7,999 < 8,000", 2, '["general"]'),
            (3, "Cual es el menor: 3,450, 3,405, 3,540?", "multiple_choice",
             '["3,450","3,405","3,540","Son iguales"]', "3,405",
             "Compara las centenas", "3,405 es el menor", 2, '["general"]'),
            (3, "4,100 __ 4,100. Que simbolo va?", "multiple_choice",
             '["<",">","=","No se sabe"]', "=", "Son el mismo numero", "4,100 = 4,100", 1, '["general"]'),
            (3, "Cual es mayor: 9,999 o 10,000?", "multiple_choice",
             '["9,999","10,000","Son iguales","No se sabe"]', "10,000",
             "10,000 tiene 5 digitos, 9,999 tiene 4", "10,000 > 9,999", 2, '["general"]'),
            (3, "Pon >, < o =: 6,543 __ 6,534", "multiple_choice",
             '["<",">","=","No se sabe"]', ">", "Las decenas: 4 vs 3", "6,543 > 6,534", 2, '["general"]'),
            (3, "Cual numero esta mas cerca de 5,000: 4,800 o 5,300?", "multiple_choice",
             '["4,800","5,300","Estan igual de cerca","No se sabe"]', "4,800",
             "4800 esta a 200 de 5000, 5300 esta a 300", "4,800 (diferencia de 200)", 3, '["general"]'),
            (3, "Cual es mayor: 2,999 o 3,001?", "multiple_choice",
             '["2,999","3,001","Son iguales","No se sabe"]', "3,001",
             "3 mil es mas que 2 mil", "3,001 > 2,999", 1, '["general"]'),
            # Skill 4: Ordenar numeros
            (4, "Ordena de menor a mayor: 500, 300, 700", "multiple_choice",
             '["300, 500, 700","500, 300, 700","700, 500, 300","300, 700, 500"]', "300, 500, 700",
             "Encuentra el mas pequeno primero", "300 < 500 < 700", 1, '["general"]'),
            (4, "Ordena de mayor a menor: 1,234, 4,321, 2,143", "multiple_choice",
             '["4,321, 2,143, 1,234","1,234, 2,143, 4,321","4,321, 1,234, 2,143","2,143, 4,321, 1,234"]',
             "4,321, 2,143, 1,234", "Encuentra el mas grande primero", "4,321 > 2,143 > 1,234", 2, '["general"]'),
            (4, "Cual numero va entre 2,340 y 2,360?", "multiple_choice",
             '["2,330","2,350","2,370","2,300"]', "2,350",
             "Busca un numero mayor que 2340 y menor que 2360", "2,340 < 2,350 < 2,360", 1, '["general"]'),
            (4, "Ordena: 8,100, 8,010, 8,001 de menor a mayor", "multiple_choice",
             '["8,001, 8,010, 8,100","8,010, 8,001, 8,100","8,100, 8,010, 8,001","8,001, 8,100, 8,010"]',
             "8,001, 8,010, 8,100", "Compara digito por digito", "8,001 < 8,010 < 8,100", 2, '["general"]'),
            (4, "Que numero va justo despues de 3,999?", "numeric", '[]', "4000",
             "Suma 1 a 3,999", "3,999 + 1 = 4,000", 1, '["general"]'),
            (4, "Que numero va justo antes de 7,000?", "numeric", '[]', "6999",
             "Resta 1 a 7,000", "7,000 - 1 = 6,999", 1, '["general"]'),
            (4, "Ordena de menor a mayor: 5,050, 5,500, 5,005", "multiple_choice",
             '["5,005, 5,050, 5,500","5,050, 5,005, 5,500","5,500, 5,050, 5,005","5,005, 5,500, 5,050"]',
             "5,005, 5,050, 5,500", "Compara centenas", "5,005 < 5,050 < 5,500", 2, '["general"]'),
            (4, "Que numero esta entre 4,500 y 4,600?", "multiple_choice",
             '["4,400","4,550","4,700","4,300"]', "4,550",
             "Busca mayor que 4500 y menor que 4600", "4,500 < 4,550 < 4,600", 1, '["general"]'),
            (4, "Ordena de mayor a menor: 9,876, 9,678, 9,768", "multiple_choice",
             '["9,876, 9,768, 9,678","9,678, 9,768, 9,876","9,876, 9,678, 9,768","9,768, 9,876, 9,678"]',
             "9,876, 9,768, 9,678", "Compara centenas: 8>7>6", "9,876 > 9,768 > 9,678", 2, '["general"]'),
            (4, "Cual es el tercer numero en orden de menor a mayor: 100, 1000, 10, 10000?", "numeric", '[]', "1000",
             "Ordena: 10, 100, 1000, 10000", "El tercero es 1,000", 2, '["general"]'),
            # Skill 5: Redondeo
            (5, "Redondea 347 a la decena mas cercana", "numeric", '[]', "350",
             "Mira el digito de las unidades: 7>=5, sube", "347 -> 350", 1, '["general"]'),
            (5, "Redondea 823 a la centena mas cercana", "numeric", '[]', "800",
             "Mira el digito de las decenas: 2<5, baja", "823 -> 800", 1, '["general"]'),
            (5, "Redondea 1,450 a la centena mas cercana", "multiple_choice",
             '["1,400","1,500","1,000","2,000"]', "1,500",
             "5 en las decenas = sube", "1,450 -> 1,500", 2, '["general"]'),
            (5, "Redondea 6,789 a la decena mas cercana", "numeric", '[]', "6790",
             "9>=5, sube la decena", "6,789 -> 6,790", 2, '["general"]'),
            (5, "Redondea 2,550 a la centena mas cercana", "numeric", '[]', "2600",
             "5 en las decenas = sube", "2,550 -> 2,600", 2, '["general"]'),
            (5, "Redondea 4,321 a la decena mas cercana", "numeric", '[]', "4320",
             "1<5, baja", "4,321 -> 4,320", 1, '["general"]'),
            (5, "Redondea 9,950 a la centena mas cercana", "numeric", '[]', "10000",
             "5 en las decenas = sube: 9,900+100=10,000", "9,950 -> 10,000", 3, '["general"]'),
            (5, "Redondea 3,333 a la centena mas cercana", "numeric", '[]', "3300",
             "3<5 en las decenas, baja", "3,333 -> 3,300", 1, '["general"]'),
            (5, "Redondea 7,865 a la decena mas cercana", "numeric", '[]', "7870",
             "5>=5, sube", "7,865 -> 7,870", 2, '["general"]'),
            (5, "Redondea 1,149 a la centena mas cercana", "multiple_choice",
             '["1,100","1,200","1,000","1,150"]', "1,100",
             "4<5, baja", "1,149 -> 1,100", 1, '["general"]'),
        ]

        for q in exercise_questions_skills_1_5:
            db.execute("""INSERT INTO questions (skill_id, question_text, question_type, options, correct_answer, hint, explanation, difficulty, is_placement, interest_tags)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)""", q)

        # ===========================================
        # EXERCISE QUESTIONS - 4to Grado (Skills 6+)
        # ===========================================
        exercise_questions_4to = [
            (6, "Cuanto es 23 + 19?", "numeric", '[]', "42", "Suma las unidades primero", "23 + 19 = 42", 1, '["general"]'),
            (6, "Cuanto es 56 + 37?", "numeric", '[]', "93", "6+7=13, lleva 1", "56 + 37 = 93", 1, '["general"]'),
            (6, "En un zoologico hay 28 monos y 35 loros. Cuantos animales hay?", "numeric", '[]', "63", "Suma 28 + 35", "28 + 35 = 63 animales", 1, '["animales"]'),
            (7, "Cuanto es 167 + 245?", "numeric", '[]', "412", "Suma columna por columna", "167 + 245 = 412", 2, '["general"]'),
            (7, "Un cohete viajo 589 km el primer dia y 673 km el segundo. Cuantos km viajo en total?", "numeric", '[]', "1262", "Suma 589 + 673", "589 + 673 = 1,262 km", 2, '["espacio"]'),
            (15, "Cuanto es 3 x 5?", "numeric", '[]', "15", "3 grupos de 5", "3 x 5 = 15", 1, '["general"]'),
            (15, "Cuanto es 4 x 4?", "numeric", '[]', "16", "4 grupos de 4", "4 x 4 = 16", 1, '["general"]'),
            (15, "Si cada dinosaurio tiene 4 patas, cuantas patas tienen 5 dinosaurios?", "numeric", '[]', "20", "Multiplica 5 x 4", "5 x 4 = 20 patas", 1, '["dinosaurios"]'),
            (16, "Cuanto es 6 x 7?", "numeric", '[]', "42", "6 x 7 es 6 x 6 + 6", "6 x 7 = 42", 2, '["general"]'),
            (16, "Cuanto es 9 x 8?", "numeric", '[]', "72", "9 x 8 = 9 x (10-2)", "9 x 8 = 72", 2, '["general"]'),
            (16, "Un musico practica 7 canciones al dia. Cuantas canciones practica en 8 dias?", "numeric", '[]', "56", "Multiplica 7 x 8", "7 x 8 = 56 canciones", 2, '["musica"]'),
            (17, "Cuanto es 34 x 10?", "numeric", '[]', "340", "Agrega un cero al final", "34 x 10 = 340", 2, '["general"]'),
            (18, "Cuanto es 23 x 14?", "numeric", '[]', "322", "23x4=92, 23x10=230, suma", "23 x 14 = 322", 3, '["general"]'),
            (23, "Si una barra de chocolate tiene 6 pedazos y te dan 2, que fraccion tienes?", "multiple_choice",
             '["2/6","4/6","6/2","2/4"]', "2/6", "Numerador = pedazos que tienes, denominador = total", "2 de 6 = 2/6", 1, '["cocina"]'),
            (23, "Que fraccion de un dia son 6 horas?", "multiple_choice",
             '["6/24","6/12","1/4","6/24 = 1/4"]', "6/24", "Un dia tiene 24 horas", "6 horas de 24 = 6/24", 1, '["general"]'),
            (27, "Cuantos lados tiene un rectangulo?", "numeric", '[]', "4", "Rec-tangulo tiene 4 angulos rectos", "4 lados", 1, '["general"]'),
            (28, "Un cuadrado tiene lados de 8 cm. Cual es su perimetro?", "numeric", '[]', "32", "P = 4 x lado", "4 x 8 = 32 cm", 2, '["general"]'),
            (29, "Una cancha de basquet mide 15m x 8m. Cual es su area?", "numeric", '[]', "120", "Area = largo x ancho", "15 x 8 = 120 m2", 3, '["deportes"]'),
        ]

        for q in exercise_questions_4to:
            db.execute("""INSERT INTO questions (skill_id, question_text, question_type, options, correct_answer, hint, explanation, difficulty, is_placement, interest_tags) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)""", q)

        # ===========================================
        # EXERCISE QUESTIONS - Kindergarten
        # ===========================================
        exercise_questions_kinder = [
            (101, "Cuenta las estrellas: * * *", "multiple_choice", '["2","3","4","5"]', "3", "Cuenta una por una", "Hay 3 estrellas", 1, '["general"]'),
            (101, "Cuantos gatos ves? (gato gato)", "multiple_choice", '["1","2","3","4"]', "2", "Cuenta cada gato", "Hay 2 gatos", 1, '["animales"]'),
            (102, "Que numero viene despues del 9?", "multiple_choice", '["8","10","11","12"]', "10", "Cuenta: 8, 9, ...", "Despues del 9 viene el 10", 1, '["general"]'),
            (102, "Cuenta: 1, 2, 3, __, 5. Que numero falta?", "multiple_choice", '["3","4","5","6"]', "4", "Lee la secuencia", "Falta el 4", 1, '["general"]'),
            (103, "Que numero viene despues del 15?", "multiple_choice", '["14","16","17","20"]', "16", "Cuenta: 14, 15, ...", "Despues del 15 viene el 16", 2, '["general"]'),
            (105, "Senala el numero 3", "multiple_choice", '["1","2","3","4"]', "3", "Busca el tres", "Este es el 3", 1, '["general"]'),
            (106, "Cual de estos es el numero 8?", "multiple_choice", '["6","7","8","9"]', "8", "El 8 parece un muneco de nieve", "Este es el 8", 1, '["general"]'),
            (108, "3 es mas que 1?", "multiple_choice", '["Si","No"]', "Si", "Piensa cual es mas grande", "3 es mas que 1", 1, '["general"]'),
            (109, "Cual es mas grande: un elefante o un raton?", "multiple_choice", '["Elefante","Raton"]', "Elefante", "Piensa en el tamano", "El elefante es mucho mas grande", 1, '["animales"]'),
            (111, "1 + 1 = ?", "multiple_choice", '["1","2","3","4"]', "2", "Levanta 1 dedo en cada mano", "1 + 1 = 2", 1, '["general"]'),
            (111, "2 + 2 = ?", "multiple_choice", '["3","4","5","6"]', "4", "Levanta 2 dedos en cada mano", "2 + 2 = 4", 1, '["general"]'),
            (112, "4 + 3 = ?", "multiple_choice", '["5","6","7","8"]', "7", "Cuenta desde 4: cinco, seis, siete", "4 + 3 = 7", 2, '["general"]'),
            (113, "Ana tiene 3 flores y le dan 4 mas. Cuantas flores tiene?", "multiple_choice", '["5","6","7","8"]', "7", "Suma 3 + 4", "3 + 4 = 7 flores", 2, '["naturaleza"]'),
            (114, "3 - 1 = ?", "multiple_choice", '["1","2","3","4"]', "2", "Si tienes 3 y quitas 1", "3 - 1 = 2", 1, '["general"]'),
            (115, "7 - 3 = ?", "multiple_choice", '["3","4","5","6"]', "4", "Cuenta hacia atras desde 7", "7 - 3 = 4", 2, '["general"]'),
            (116, "Una pelota tiene forma de...", "multiple_choice", '["Cuadrado","Circulo","Triangulo","Rectangulo"]', "Circulo", "Es redonda", "Una pelota es redonda como un circulo", 1, '["deportes"]'),
            (117, "Una puerta tiene forma de...", "multiple_choice", '["Circulo","Triangulo","Rectangulo","Estrella"]', "Rectangulo", "Es alta y tiene esquinas", "Una puerta tiene forma de rectangulo", 1, '["general"]'),
            (119, "Completa: circulo, cuadrado, circulo, cuadrado, ...", "multiple_choice", '["circulo","cuadrado","triangulo","rectangulo"]', "circulo", "El patron se repite", "Sigue circulo", 1, '["general"]'),
            (120, "Completa: grande, pequeno, grande, pequeno, ...", "multiple_choice", '["grande","mediano","pequeno","igual"]', "grande", "Observa el patron", "Se repite grande, pequeno", 2, '["general"]'),
        ]

        for q in exercise_questions_kinder:
            db.execute("""INSERT INTO questions (skill_id, question_text, question_type, options, correct_answer, hint, explanation, difficulty, is_placement, interest_tags) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)""", q)

        # Create lessons for each skill - 4to Grado
        for s in skills_data_4to:
            db.execute("INSERT INTO lessons (skill_id, title, description, difficulty, estimated_minutes) VALUES (?, ?, ?, ?, ?)",
                       (s[0], f"Leccion: {s[1]}", s[2], s[4], 5))

        # Create lessons for each skill - Kinder
        for s in skills_data_kinder:
            db.execute("INSERT INTO lessons (skill_id, title, description, difficulty, estimated_minutes) VALUES (?, ?, ?, ?, ?)",
                       (s[0], f"Leccion: {s[1]}", s[2], s[4], 3))

        # Create some mastery signals for existing students (simulate some progress)
        mastery_data = [
            (1, 1, 0.95, 10, 9),
            (1, 2, 0.85, 8, 7),
            (1, 6, 0.90, 12, 11),
            (1, 7, 0.75, 8, 6),
            (1, 11, 0.88, 10, 9),
            (1, 15, 0.92, 15, 14),
        ]
        mastery_data += [
            (2, 1, 0.90, 8, 7),
            (2, 6, 0.95, 10, 9),
            (2, 7, 0.80, 6, 5),
            (2, 11, 0.70, 10, 7),
            (2, 15, 0.60, 5, 3),
        ]
        mastery_data += [
            (3, 1, 0.88, 8, 7),
            (3, 2, 0.90, 10, 9),
            (3, 6, 0.85, 8, 7),
            (3, 11, 0.92, 12, 11),
        ]

        for m in mastery_data:
            db.execute("""INSERT INTO mastery_signals (student_id, skill_id, mastery_level, attempts_count, correct_count, last_practiced)
                         VALUES (?, ?, ?, ?, ?, datetime('now'))""", m)

        # Mark first 3 students as having completed placement test
        for sid in [1, 2, 3]:
            db.execute("UPDATE students SET placement_test_completed = 1, placement_test_score = ? WHERE id = ?",
                       (85.0 + sid * 2, sid))

        # Create some daily sessions
        db.execute("""INSERT INTO daily_sessions (student_id, target_skill_id, mission_title, status, total_questions, correct_answers, active_time_seconds, session_date)
                     VALUES (1, 7, 'Domina la suma con reagrupacion', 'completed', 10, 8, 1200, date('now'))""")
        db.execute("""INSERT INTO daily_sessions (student_id, target_skill_id, mission_title, status, total_questions, correct_answers, active_time_seconds, session_date)
                     VALUES (2, 15, 'Aprende las tablas del 1 al 5', 'in_progress', 8, 5, 900, date('now'))""")
        db.execute("""INSERT INTO daily_sessions (student_id, target_skill_id, mission_title, status, total_questions, correct_answers, active_time_seconds, session_date)
                     VALUES (3, 11, 'Practica la resta basica', 'completed', 12, 11, 1100, date('now'))""")

        # Create sample messages
        db.execute("""INSERT INTO messages (sender_id, receiver_id, student_id, subject, body)
                     VALUES (2, 14, 1, 'Progreso de Sofia', 'Sofia tuvo un excelente dia hoy. Domino la suma con reagrupacion sin ayuda.')""")

        # Achievements
        db.execute("INSERT INTO achievements (student_id, title, description, icon) VALUES (1, 'Primera Mision', 'Completaste tu primera mision diaria', 'target')")
        db.execute("INSERT INTO achievements (student_id, title, description, icon) VALUES (1, 'Racha de 3', 'Tres respuestas correctas seguidas', 'fire')")
        db.execute("INSERT INTO achievements (student_id, title, description, icon) VALUES (2, 'Explorador', 'Completaste el placement test', 'map')")

        # ===========================================
        # KINDER VISUAL + AUDIO MEDIA (PRD §14)
        # ===========================================
        _seed_kinder_media(db)

        print("Database seeded successfully!")


def _seed_kinder_media(db):
    """Populate question_image_url, options_media, grade_level, locale for every kinder question.

    Uses emoji-based visual representations so kinder students can answer
    without reading text. Each question gets:
      - question_image_url: an emoji string representing the visual prompt
      - options_media: JSON array of {id, label, image} per option
      - grade_level: 'K'
      - locale: 'es-419'
    """
    # Map question_text prefix → visual data
    kinder_visuals = {
        # --- Placement test questions ---
        "Cuantas manzanas hay": {
            "image": "🍎🍎🍎",
            "options": [
                {"id": "1", "label": "1", "image": "🍎"},
                {"id": "2", "label": "2", "image": "🍎🍎"},
                {"id": "3", "label": "3", "image": "🍎🍎🍎"},
                {"id": "4", "label": "4", "image": "🍎🍎🍎🍎"},
            ],
        },
        "Cuantos dedos hay en una mano": {
            "image": "✋",
            "options": [
                {"id": "3", "label": "3", "image": "3️⃣"},
                {"id": "4", "label": "4", "image": "4️⃣"},
                {"id": "5", "label": "5", "image": "5️⃣"},
                {"id": "10", "label": "10", "image": "🔟"},
            ],
        },
        "Que numero viene despues del 7": {
            "image": "6️⃣ 7️⃣ ❓",
            "options": [
                {"id": "6", "label": "6", "image": "6️⃣"},
                {"id": "8", "label": "8", "image": "8️⃣"},
                {"id": "9", "label": "9", "image": "9️⃣"},
                {"id": "10", "label": "10", "image": "🔟"},
            ],
        },
        "Cual es el numero 4": {
            "image": "❓ Encuentra el 4",
            "options": [
                {"id": "2", "label": "2", "image": "2️⃣"},
                {"id": "3", "label": "3", "image": "3️⃣"},
                {"id": "4", "label": "4", "image": "4️⃣"},
                {"id": "5", "label": "5", "image": "5️⃣"},
            ],
        },
        "Donde hay MAS pelotas": {
            "image": "⚽⚽  vs  ⚽⚽⚽⚽⚽",
            "options": [
                {"id": "Grupo A", "label": "Grupo A", "image": "⚽⚽"},
                {"id": "Grupo B", "label": "Grupo B", "image": "⚽⚽⚽⚽⚽"},
                {"id": "Son iguales", "label": "Iguales", "image": "⚖️"},
                {"id": "No se sabe", "label": "No se", "image": "❓"},
            ],
        },
        "Si tienes 2 galletas y te dan 1 mas": {
            "image": "🍪🍪 ➕ 🍪",
            "options": [
                {"id": "1", "label": "1", "image": "🍪"},
                {"id": "2", "label": "2", "image": "🍪🍪"},
                {"id": "3", "label": "3", "image": "🍪🍪🍪"},
                {"id": "4", "label": "4", "image": "🍪🍪🍪🍪"},
            ],
        },
        "Cuanto es 3 + 2": {
            "image": "⭐⭐⭐ ➕ ⭐⭐",
            "options": [
                {"id": "4", "label": "4", "image": "4️⃣"},
                {"id": "5", "label": "5", "image": "5️⃣"},
                {"id": "6", "label": "6", "image": "6️⃣"},
                {"id": "7", "label": "7", "image": "7️⃣"},
            ],
        },
        "Tienes 4 globos y se revienta 1": {
            "image": "🎈🎈🎈🎈 ➖ 💥",
            "options": [
                {"id": "1", "label": "1", "image": "🎈"},
                {"id": "2", "label": "2", "image": "🎈🎈"},
                {"id": "3", "label": "3", "image": "🎈🎈🎈"},
                {"id": "4", "label": "4", "image": "🎈🎈🎈🎈"},
            ],
        },
        "Cual de estas figuras es un circulo": {
            "image": "🔍 Encuentra la figura",
            "options": [
                {"id": "Cuadrado", "label": "Cuadrado", "image": "🟧"},
                {"id": "Triangulo", "label": "Triangulo", "image": "🔺"},
                {"id": "Circulo", "label": "Circulo", "image": "🔵"},
                {"id": "Rectangulo", "label": "Rectangulo", "image": "🟩"},
            ],
        },
        "Cuantos lados tiene un cuadrado": {
            "image": "🟧",
            "options": [
                {"id": "2", "label": "2", "image": "2️⃣"},
                {"id": "3", "label": "3", "image": "3️⃣"},
                {"id": "4", "label": "4", "image": "4️⃣"},
                {"id": "5", "label": "5", "image": "5️⃣"},
            ],
        },
        "Si el patron es: rojo, azul, rojo, azul": {
            "image": "🔴🔵🔴🔵 ❓",
            "options": [
                {"id": "rojo", "label": "rojo", "image": "🔴"},
                {"id": "azul", "label": "azul", "image": "🔵"},
                {"id": "verde", "label": "verde", "image": "🟢"},
                {"id": "amarillo", "label": "amarillo", "image": "🟡"},
            ],
        },
        # --- Exercise questions ---
        "Cuenta las estrellas": {
            "image": "⭐⭐⭐",
            "options": [
                {"id": "2", "label": "2", "image": "⭐⭐"},
                {"id": "3", "label": "3", "image": "⭐⭐⭐"},
                {"id": "4", "label": "4", "image": "⭐⭐⭐⭐"},
                {"id": "5", "label": "5", "image": "⭐⭐⭐⭐⭐"},
            ],
        },
        "Cuantos gatos ves": {
            "image": "🐱🐱",
            "options": [
                {"id": "1", "label": "1", "image": "🐱"},
                {"id": "2", "label": "2", "image": "🐱🐱"},
                {"id": "3", "label": "3", "image": "🐱🐱🐱"},
                {"id": "4", "label": "4", "image": "🐱🐱🐱🐱"},
            ],
        },
        "Que numero viene despues del 9": {
            "image": "8️⃣ 9️⃣ ❓",
            "options": [
                {"id": "8", "label": "8", "image": "8️⃣"},
                {"id": "10", "label": "10", "image": "🔟"},
                {"id": "11", "label": "11", "image": "1️⃣1️⃣"},
                {"id": "12", "label": "12", "image": "1️⃣2️⃣"},
            ],
        },
        "Cuenta: 1, 2, 3, __, 5": {
            "image": "1️⃣ 2️⃣ 3️⃣ ❓ 5️⃣",
            "options": [
                {"id": "3", "label": "3", "image": "3️⃣"},
                {"id": "4", "label": "4", "image": "4️⃣"},
                {"id": "5", "label": "5", "image": "5️⃣"},
                {"id": "6", "label": "6", "image": "6️⃣"},
            ],
        },
        "Que numero viene despues del 15": {
            "image": "1️⃣4️⃣  1️⃣5️⃣  ❓",
            "options": [
                {"id": "14", "label": "14", "image": "1️⃣4️⃣"},
                {"id": "16", "label": "16", "image": "1️⃣6️⃣"},
                {"id": "17", "label": "17", "image": "1️⃣7️⃣"},
                {"id": "20", "label": "20", "image": "2️⃣0️⃣"},
            ],
        },
        "Senala el numero 3": {
            "image": "❓ Encuentra el 3",
            "options": [
                {"id": "1", "label": "1", "image": "1️⃣"},
                {"id": "2", "label": "2", "image": "2️⃣"},
                {"id": "3", "label": "3", "image": "3️⃣"},
                {"id": "4", "label": "4", "image": "4️⃣"},
            ],
        },
        "Cual de estos es el numero 8": {
            "image": "❓ Encuentra el 8",
            "options": [
                {"id": "6", "label": "6", "image": "6️⃣"},
                {"id": "7", "label": "7", "image": "7️⃣"},
                {"id": "8", "label": "8", "image": "8️⃣"},
                {"id": "9", "label": "9", "image": "9️⃣"},
            ],
        },
        "3 es mas que 1": {
            "image": "🍎🍎🍎  vs  🍎",
            "options": [
                {"id": "Si", "label": "Si", "image": "✅"},
                {"id": "No", "label": "No", "image": "❌"},
            ],
        },
        "Cual es mas grande: un elefante o un raton": {
            "image": "🐘  vs  🐭",
            "options": [
                {"id": "Elefante", "label": "Elefante", "image": "🐘"},
                {"id": "Raton", "label": "Raton", "image": "🐭"},
            ],
        },
        "1 + 1 = ?": {
            "image": "🌟 ➕ 🌟",
            "options": [
                {"id": "1", "label": "1", "image": "🌟"},
                {"id": "2", "label": "2", "image": "🌟🌟"},
                {"id": "3", "label": "3", "image": "🌟🌟🌟"},
                {"id": "4", "label": "4", "image": "🌟🌟🌟🌟"},
            ],
        },
        "2 + 2 = ?": {
            "image": "🐟🐟 ➕ 🐟🐟",
            "options": [
                {"id": "3", "label": "3", "image": "🐟🐟🐟"},
                {"id": "4", "label": "4", "image": "🐟🐟🐟🐟"},
                {"id": "5", "label": "5", "image": "🐟🐟🐟🐟🐟"},
                {"id": "6", "label": "6", "image": "🐟🐟🐟🐟🐟🐟"},
            ],
        },
        "4 + 3 = ?": {
            "image": "🍓🍓🍓🍓 ➕ 🍓🍓🍓",
            "options": [
                {"id": "5", "label": "5", "image": "5️⃣"},
                {"id": "6", "label": "6", "image": "6️⃣"},
                {"id": "7", "label": "7", "image": "7️⃣"},
                {"id": "8", "label": "8", "image": "8️⃣"},
            ],
        },
        "Ana tiene 3 flores y le dan 4 mas": {
            "image": "🌸🌸🌸 ➕ 🌸🌸🌸🌸",
            "options": [
                {"id": "5", "label": "5", "image": "5️⃣"},
                {"id": "6", "label": "6", "image": "6️⃣"},
                {"id": "7", "label": "7", "image": "7️⃣"},
                {"id": "8", "label": "8", "image": "8️⃣"},
            ],
        },
        "3 - 1 = ?": {
            "image": "🎈🎈🎈 ➖ 🎈",
            "options": [
                {"id": "1", "label": "1", "image": "🎈"},
                {"id": "2", "label": "2", "image": "🎈🎈"},
                {"id": "3", "label": "3", "image": "🎈🎈🎈"},
                {"id": "4", "label": "4", "image": "🎈🎈🎈🎈"},
            ],
        },
        "7 - 3 = ?": {
            "image": "🌟🌟🌟🌟🌟🌟🌟 ➖ 🌟🌟🌟",
            "options": [
                {"id": "3", "label": "3", "image": "3️⃣"},
                {"id": "4", "label": "4", "image": "4️⃣"},
                {"id": "5", "label": "5", "image": "5️⃣"},
                {"id": "6", "label": "6", "image": "6️⃣"},
            ],
        },
        "Una pelota tiene forma de": {
            "image": "⚽ Que forma es?",
            "options": [
                {"id": "Cuadrado", "label": "Cuadrado", "image": "🟧"},
                {"id": "Circulo", "label": "Circulo", "image": "🔵"},
                {"id": "Triangulo", "label": "Triangulo", "image": "🔺"},
                {"id": "Rectangulo", "label": "Rectangulo", "image": "🟩"},
            ],
        },
        "Una puerta tiene forma de": {
            "image": "🚪 Que forma es?",
            "options": [
                {"id": "Circulo", "label": "Circulo", "image": "🔵"},
                {"id": "Triangulo", "label": "Triangulo", "image": "🔺"},
                {"id": "Rectangulo", "label": "Rectangulo", "image": "🟩"},
                {"id": "Estrella", "label": "Estrella", "image": "⭐"},
            ],
        },
        "Completa: circulo, cuadrado, circulo, cuadrado": {
            "image": "🔵🟧🔵🟧 ❓",
            "options": [
                {"id": "circulo", "label": "circulo", "image": "🔵"},
                {"id": "cuadrado", "label": "cuadrado", "image": "🟧"},
                {"id": "triangulo", "label": "triangulo", "image": "🔺"},
                {"id": "rectangulo", "label": "rectangulo", "image": "🟩"},
            ],
        },
        "Completa: grande, pequeno, grande, pequeno": {
            "image": "🐘🐭🐘🐭 ❓",
            "options": [
                {"id": "grande", "label": "grande", "image": "🐘"},
                {"id": "mediano", "label": "mediano", "image": "🐕"},
                {"id": "pequeno", "label": "pequeno", "image": "🐭"},
                {"id": "igual", "label": "igual", "image": "⚖️"},
            ],
        },
    }

    # Update all kinder questions with visual data
    kinder_qs = db.execute(
        "SELECT id, question_text FROM questions WHERE skill_id >= 101 AND skill_id <= 120"
    ).fetchall()

    for q in kinder_qs:
        q_text = q["question_text"]
        visual = None
        for prefix, data in kinder_visuals.items():
            if q_text.startswith(prefix):
                visual = data
                break

        if visual:
            db.execute(
                """UPDATE questions
                   SET question_image_url = ?,
                       options_media = ?,
                       grade_level = 'K',
                       locale = 'es-419'
                   WHERE id = ?""",
                (
                    visual["image"],
                    json.dumps(visual["options"], ensure_ascii=False),
                    q["id"],
                ),
            )
        else:
            # Still mark as kinder even without visual match
            db.execute(
                "UPDATE questions SET grade_level = 'K', locale = 'es-419' WHERE id = ?",
                (q["id"],),
            )
