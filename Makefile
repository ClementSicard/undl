QUERY := "Evaluation of women and peace and security in field-based missions : elections and political transitions : report of the Office of Internal Oversight Services"
QUERY_OUTPUT := downloads/output_query.json

ID := 515307
ID_OUTPUT := downloads/output_id.json

query:
	poetry run python main.py 	\
		-q ${QUERY} 				\
		-o ${QUERY_OUTPUT} 			\
		-v

id:
	poetry run python main.py 	\
		--id ${ID} 				\
		-o ${ID_OUTPUT} 			\
		-v
