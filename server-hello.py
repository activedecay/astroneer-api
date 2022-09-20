from flask import Flask, request
from flask_restx import Resource, Api, reqparse, fields

app = Flask(__name__)
api = Api(app)

todoModel = api.model('TodoModel', {
    'task': fields.String,
    'uri': fields.Url('todo_ep')
})


class TodoDao(object):
    def __init__(self, todo_id, task):
        self.todo_id = todo_id
        self.task = task

        # This field will not be sent in the response
        self.status = 'active'

#
# todos = {'lmao': 1}
#
#
# # @api.route('/hello', '/world')
class HelloWorld(Resource):
    @api.marshal_with(todoModel)
    def post(self):
        parser = reqparse.RequestParser()
        # http post body arguments parser here declares that the body must contain a rate
        parser.add_argument('rate', type=int, help='Rate to charge for this resource')
        args = parser.parse_args(strict=True)
        return TodoDao(todo_id='my_todo', task='Remember the milk')


#
#
# # or
#
api.add_resource(HelloWorld, '/hello')
# api.add_resource(HelloWorld, '/todo/<int:todo_id>', endpoint='todo_ep')

# @api.route('/<string:todo_id>')
# class TodoSimple(Resource):
#     def get(self, todo_id):
#         return {todo_id: todos[todo_id]}
#
#     def put(self, todo_id):
#         todos[todo_id] = request.form['data']
#         return {todo_id: todos[todo_id]}
#
#
# class Todo1(Resource):
#     def get(self):
#         # Default to 200 OK
#         return {'task': 'Hello world'}
#
#
# class Todo2(Resource):
#     def get(self):
#         # Set the response code to 201
#         return {'task': 'Hello world'}, 201
#
#
# class Todo3(Resource):
#     def get(self):
#         # Set the response code to 201 and return custom headers
#         return {'task': 'Hello world'}, 201, {'Etag': 'some-opaque-string'}



if __name__ == '__main__':
    app.run(debug=True)
