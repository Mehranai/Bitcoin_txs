from neo4j import GraphDatabase

driver = GraphDatabase.driver("neo4j://127.0.0.1:7687", auth=("neo4j", "mehran.boxer8"))

with driver.session(database="task1") as session:
    result = session.run("RETURN 'Connected to task1!' AS msg")
    print(result.single()["msg"])
