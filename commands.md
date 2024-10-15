<!-- if not created -->
alembic init alembic

pip freeze > requirements.txt 

<!-- docker -->
docker-compose up
docker-compose build
docker-compose build --no-cache

<!-- for migrations -->
docker-compose run app alembic revision --autogenerate -m "New Migration" 
docker-compose run app alembic upgrade head

<!-- queries -->
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

<!-- mutations -->
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




<!-- notes -->
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