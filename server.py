from flask import Flask
from flask_restx import Api, Resource, fields
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.config['RESTX_MASK_SWAGGER'] = False
app.wsgi_app = ProxyFix(app.wsgi_app)
api = Api(app, version="1.0.0", title="astroneer", description="An astroneer app", prefix='/astro/v1')

ns = api.namespace("astroneer", description="Astroneer operations")  # todo why have namespaces at all?

DATABASE = {'modules': [], 'resources': [], 'planets': []}

resource_model = api.model("Resource", {
    "name": fields.String(required=True, description="The name of the resource"),
    "found": fields.List(fields.String, required=True, description="Planets on which this resource is found")
})
resource_list = api.model("ResourceList", {
    "resources": fields.List(fields.Nested(resource_model, description="Resource"), description="Resources"),
})

module_model = api.model("Module", {
    "name": fields.String(required=True, description="The name of the module"),
    "resource_cost": fields.List(fields.String, description="Resource cost to craft the module in a printer")
})
module_list = api.model("ModuleList", {
    "modules": fields.List(fields.Nested(module_model, description="Module"), description="Modules"),
})


def abort_if_module(module, **kwargs):
    test = [x['name'] for x in DATABASE['modules'] if x['name'] == module]
    if 'not_exists' in kwargs:
        test = not test
        api.abort(404, "module {} doesn't exist".format(module))
    if test:  # if empty, 404
        api.abort(400, "Module {} already exists".format(module))


def abort_if_resource(resource, **kwargs):
    test = [x['name'] for x in DATABASE['resources'] if x['name'] == resource]
    if 'not_exists' in kwargs:
        test = not test
        api.abort(404, "resource {} doesn't exist".format(resource))
    if test:  # if empty, 404
        api.abort(400, "Resource {} already exists".format(resource))


@ns.route("/")
class Debug(Resource):

    def get(self):
        """Debug print"""
        return DATABASE


resource_parser = api.parser()
resource_parser.add_argument("name", type=str, required=True, help="Resource name", location="form")
resource_parser.add_argument("found", type=str, required=True, help="Planets on which this resource is found",
                             location="form")
module_parser = api.parser()
module_parser.add_argument("name", type=str, required=True, help="Resource name", location="form")
module_parser.add_argument("resource_cost", type=str, required=True, help="Resource cost to print the module",
                           location="form")


#
# resources
#


@ns.route("/resource/<string:name_id>")
@api.doc(responses={404: "Resource not found"}, params={"name_id": "The resource name"})
class ResourceApi(Resource):
    """Show a single todo item and lets you delete them"""

    @api.doc(description="Resource name should be in the database")
    @api.marshal_with(resource_model)
    def get(self, name_id):
        """Fetch a given resource"""
        abort_if_resource(name_id, not_exists=True)
        return [x for x in DATABASE['resources'] if x['name'] == name_id][0]

    @api.doc(responses={204: "Resource deleted"})
    def delete(self, name_id):
        """Delete a given resource"""

        abort_if_resource(name_id, not_exists=True)
        DATABASE['resources'].remove([x for x in DATABASE['resources'] if x['name'] == name_id][0])
        return "", 204

    @api.doc(parser=resource_parser)
    @api.marshal_with(resource_model)
    def put(self, name_id):
        """Update a given resource"""
        abort_if_resource(name_id, not_exists=True)
        args = resource_parser.parse_args()
        resource = {
            "name": args["name"],
            "found": [x.strip() for x in args["found"].split(',')]
        }
        DATABASE['resources'].remove([x for x in DATABASE['resources'] if x['name'] == name_id][0])
        DATABASE['resources'].append(resource)
        return resource


@ns.route("/resource/")
class ResourceListApi(Resource):
    """Shows a list of all resources, and lets you POST to add new resources"""

    @api.marshal_list_with(resource_list)
    def get(self):
        """List all resources"""
        return {'resources': DATABASE['resources']}

    @api.doc(parser=resource_parser, responses={400: "Module already exists"})
    @api.marshal_with(resource_model, code=201)
    def post(self):
        """Create a resource"""
        args = resource_parser.parse_args()
        abort_if_resource(args["name"], exists=True)
        resource = {
            "name": args["name"],
            "found": [x.strip() for x in args["found"].split(',')]
        }
        DATABASE['resources'].append(resource)
        return resource, 201


#
# modules
#


@ns.route("/module/<string:name_id>")
@api.doc(responses={404: "Module not found"}, params={"name_id": "The module name"})
class ModuleApi(Resource):
    """Show a single todo item and lets you delete them"""

    @api.doc(description="Module name should be in the database")
    @api.marshal_with(module_model)
    def get(self, name_id):
        """Fetch a given module"""
        abort_if_module(name_id, not_exists=True)
        return [x for x in DATABASE['modules'] if x['name'] == name_id][0]

    @api.doc(responses={204: "Module deleted"})
    def delete(self, name_id):
        """Delete a given module"""

        abort_if_module(name_id, not_exists=True)
        DATABASE['modules'].remove([x for x in DATABASE['modules'] if x['name'] == name_id][0])
        return "", 204

    @api.doc(parser=module_parser)
    @api.marshal_with(module_model)
    def put(self, name_id):
        """Update a given module"""

        abort_if_module(name_id, not_exists=True)
        args = module_parser.parse_args()
        module = {
            "name": args["name"],
            "found": [x.strip() for x in args["found"].split(',')]
        }
        DATABASE['modules'].remove([x for x in DATABASE['modules'] if x['name'] == name_id][0])
        DATABASE['modules'].append(module)
        return module


@ns.route("/module/")
class ModuleListApi(Resource):
    """Shows a list of all modules, and lets you POST to add new modules"""

    @api.marshal_list_with(module_list)
    def get(self):
        """List all modules"""
        return {'modules': DATABASE['modules']}

    @api.doc(parser=module_parser, responses={400: "Module already exists"})
    @api.marshal_with(module_model, code=201)
    def post(self):
        """Create a module"""
        args = module_parser.parse_args()
        abort_if_module(args["name"], exists=True)
        module = {
            "name": args["name"],
            "resource_cost": [x.strip() for x in args["resource_cost"].split(',')]
        }
        DATABASE['modules'].append(module)
        return module, 201


if __name__ == "__main__":
    app.run(debug=True)
