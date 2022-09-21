"""cool"""
import csv
import sys

import flask
from flask_restx import Api, Resource, fields
from werkzeug.middleware.proxy_fix import ProxyFix

app = flask.Flask(__name__)
app.config['RESTX_MASK_SWAGGER'] = False
app.wsgi_app = ProxyFix(app.wsgi_app)
api = Api(app, version="1.0.0", title="Astroneer",
          description="An Astroneer API by the chunkinator, dude", prefix='/astro/v1')

# it appears that the only reason to have a namespace is to further segregate the swagger ui
ns = api.namespace("Default", description="Default operations")
resource_ns = api.namespace("Resources", description="Astroneer resources operations")
module_ns = api.namespace("Modules", description="Astroneer modules operations")

DATABASE = {'modules': [], 'resources': [], 'planets': []}

module_model = api.model("Module", {
    "name": fields.String(required=True,
                          description="The name of the module"),
    "resource_cost": fields.List(fields.String,
                                 description="Resource cost to craft the module in a printer"),
    "printer": fields.String(required=True,
                             description="Printer used to create this module")
})
module_list = api.model("ModuleList", {
    "modules": fields.List(fields.Nested(module_model,
                                         description="Module"),
                           description="Modules"),
})

resource_model = api.model("Resource", {
    "name": fields.String(required=True,
                          description="The name of the resource"),
    "found": fields.List(fields.String,
                         description="Planets on which this resource is found"),
    "crafted_in": fields.List(fields.String(description="Module"),
                              description="Modules used to craft this resource"),
    "refined_with": fields.List(fields.String(description="Resource"),
                                description="Resources used to refine this resource"),
    "rate": fields.List(fields.String(description="Planet resource collection rate"),
                        description="Resource collection rate in an Atmospheric Condenser")
})
resource_list = api.model("ResourceList", {
    "resources": fields.List(fields.Nested(resource_model,
                                           description="Resource"),
                             description="Resources"),
})

planet_model = api.model("Planet", {
    "name": fields.String(required=True,
                          description="The name of the planet"),
})
planet_list = api.model("PlanetList", {
    "planets": fields.List(fields.Nested(planet_model,
                                         description="Planet"),
                           description="Planets"),
})


def abort_if_module(module, **kwargs):
    """ Aborting protocol
    :key not_exists when true abort if name does not exist
    """
    test = [x['name'] for x in DATABASE['modules'] if x['name'] == module]
    if 'not_exists' in kwargs:
        if not test:
            api.abort(404, f"Module {module} doesn't exist")
        else:
            return
    if test:  # if empty, 404
        api.abort(400, f"Module {module} already exists")


def abort_if_resource(resource, **kwargs):
    """ Aborting protocol
    :key not_exists when true abort if name does not exist
    """
    test = [x['name'] for x in DATABASE['resources'] if x['name'] == resource]
    if 'not_exists' in kwargs:
        if not test:
            api.abort(404, f"Resource {resource} doesn't exist")
        else:
            return
    if test:  # if empty, 404
        api.abort(400, f"Resource {resource} already exists")


@ns.route("/")
class Debug(Resource):
    """Simple debug resource to aid in development"""

    def get(self):
        """Debug print"""
        return DATABASE


resource_parser = api.parser()
resource_parser.add_argument("name", type=str, required=True, help="Resource name", location="form")
resource_parser.add_argument("found", type=str,
                             help="Planets on which this resource is found",
                             location="form")
resource_parser.add_argument("crafted_in", type=str,
                             help="Modules used to craft this resource",
                             location="form")
resource_parser.add_argument("refined_with", type=str,
                             help="Resources used to refine this resource",
                             location="form")
resource_parser.add_argument("rate", type=str,
                             help="Resource collection rate in an Atmospheric Condenser",
                             location="form")
module_parser = api.parser()
module_parser.add_argument("name", type=str, required=True,
                           help="Resource name", location="form")
module_parser.add_argument("resource_cost", type=str, required=True,
                           help="Resource cost to print the module",
                           location="form")
module_parser.add_argument("printer", type=str, required=True,
                           help="Printer used to create this module",
                           location="form")


#
# resources
#


@resource_ns.route("/<string:name_id>")
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
            'name': args["name"],
            'found': [x.strip() for x in args["found"].split(',')
                      ] if 'found' in args else [],
            'crafted_in': [x.strip() for x in args['crafted_in'].split(',')
                           ] if 'crafted_in' in args else []
        }
        DATABASE['resources'].remove([x for x in DATABASE['resources'] if x['name'] == name_id][0])
        DATABASE['resources'].append(resource)
        return resource


@resource_ns.route("/")
class ResourceListApi(Resource):
    """Shows a list of all resources, and lets you POST to add new resources"""

    # rate should be `planet:rate`
    def hydrate(self, name, found=None, crafted_in=None, refined_with=None, rate=None):
        """Resource database is hydrated from csv files"""
        resource = {
            'name': name,
            'found': [x.strip() for x in found.split(',')
                      ] if found else [],
            'crafted_in': [x.strip() for x in crafted_in.split(',')
                           ] if crafted_in else [],
            'refined_with': [x.strip() for x in refined_with.split(',')
                             ] if refined_with else [],
            'rate': [x.strip() for x in rate.split(',')
                     ] if rate else [],
        }
        DATABASE['resources'].append(resource)

    @api.marshal_list_with(resource_list)
    def get(self):
        """List all resources"""
        return {'resources': DATABASE['resources']}

    @api.doc(parser=resource_parser, responses={400: "Resource already exists"})
    @api.marshal_with(resource_model, code=201)
    def post(self):
        """Create a resource"""
        args = resource_parser.parse_args()
        abort_if_resource(args["name"], exists=True)
        resource = {
            'name': args["name"],
            'found': [x.strip() for x in args["found"].split(',')
                      ] if 'found' in args else [],
            'crafted_in': [x.strip() for x in args['crafted_in'].split(',')
                           ] if 'crafted_in' in args else []
        }
        DATABASE['resources'].append(resource)
        return resource, 201


#
# modules
#


@module_ns.route("/<string:name_id>")
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
        # need a good attribute replacement pattern for puts to update only some attributes
        module = {
            "name": args["name"],
            "resource_cost": [x.strip() for x in args["resource_cost"].split(',')],
            "printer": args["printer"]
        }
        DATABASE['modules'].remove([x for x in DATABASE['modules'] if x['name'] == name_id][0])
        DATABASE['modules'].append(module)
        return module


@module_ns.route("/")
class ModuleListApi(Resource):
    """Shows a list of all modules, and lets you POST to add new modules"""

    def hydrate(self, name, resource_cost, printer):
        """Hydrate the database with modules"""
        module = {
            "name": name,
            "resource_cost": resource_cost,
            "printer": printer
        }
        DATABASE['modules'].append(module)

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
            "resource_cost": [x.strip() for x in args["resource_cost"].split(',')],
            "printer": args["printer"]
        }
        DATABASE['modules'].append(module)
        return module, 201


if __name__ == "__main__":
    DEBUG = False
    if 'debug' in sys.argv:
        DEBUG = True
    MODULES = ['data/printing0.csv', 'data/printing1.csv', 'data/printing2.csv',
               'data/printing3.csv']
    PRINTERS = ['Backpack Printer', 'Small Printer', 'Medium Printer', 'Large Printer']
    for FILE, PRINTER in zip(MODULES, PRINTERS):
        with open(FILE, newline='', encoding='utf8') as f:
            READER = csv.reader(f)
            MODULE_HYDRATOR = ModuleListApi()
            for r in READER:  # row
                MODULE_HYDRATOR.hydrate(r[0], [r[1]], PRINTER)
    with open('data/resources.csv', newline='', encoding='utf8') as f:
        READER = csv.reader(f)
        RESOURCE_HYDRATOR = ResourceListApi()
        for r in READER:
            RESOURCE_HYDRATOR.hydrate(r[0], r[1], r[2], r[3], r[4])

    app.run(debug=DEBUG)
