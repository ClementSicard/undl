QUERY := "Evaluation of women and peace and security in field-based missions : elections and political transitions : report of the Office of Internal Oversight Services"
OUTPUT := downloads/output.json

test:
	poetry run python main.py 	\
		${QUERY} 				\
		-o ${OUTPUT} 			\
		-v
