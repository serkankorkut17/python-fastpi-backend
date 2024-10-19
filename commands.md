# USEFUL COMMANDS

### Activate venv
python3 -m venv venv
<br>
pip install -r requirements. txt
<br>
source venv/bin/activate

---

### Generate requirements.txt
pip freeze > requirements.txt 

---

### Run main.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

---

### Docker Specific
docker-compose up
<br>
docker-compose build
<br>
docker-compose build --no-cache

---

### If not created
alembic init alembic

---

### For migrations with docker
docker-compose run app alembic revision --autogenerate -m "New Migration"
<br>
docker-compose run app alembic upgrade head

---

### For migrations 
alembic revision --autogenerate -m "comment"
<br>
alembic upgrade head

---

### Queries
query User{
  userById(
    userId:1
  ) {
    id
    username
    email
	roleId
    role
    createdAt
    updatedAt
    lastLogin
    posts
  }
}
query{ allPosts{ title } }

query{ postById(postId:2){ id title content } }

---

### Mutations
mutation CreateRole {
    createRole(name:"Admin", description:"Administrator role with full permissions") {
        ok,
        roleId
    }
}

mutation CreateUser {
    createUser(username:"test", email:"test@test.com", roleId:1, password:"password") {
        ok,
        userId
    }
}


mutation Login {
    login(username:"test", password:"password") {
        ok,
        accessToken
    }
}

mutation CreatePost {
    createPost(title:"a title", content:"a content") {
        ok,
        postId
    }
}

---

### Notes
Amazing tutorial.
If you're coming here in 2023, here's a couple of things you need to know.
1. graphql is no longer accessible through starlette, use from starlette_graphene3 import GraphQLApp
2. app.add_route is nolonger valid, use app.mount
3. to get the GUI, you'll need make_graphiql_handler() from starlette_graphene3.

Your imports should be: 
from starlette_graphene3 import GraphQLApp, make_graphiql_handler

your route method should be:
app.mount("/graphql",GraphQLApp(schema=graphene.Schema(query=Query, mutation=PostMutations),on_get=make_graphiql_handler()))

Another note from my headbanging - you would also need the 3.x version of graphene-sqlalchemy by running pip install --pre "graphene-sqlalchemy" as the standard install gets version < 3.
