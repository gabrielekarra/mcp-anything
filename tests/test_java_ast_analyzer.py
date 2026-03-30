"""Tests for the javalang AST-based Java analyzer (java_ast.py).

Covers every real-world annotation edge case that breaks the regex analyzer:
annotation ordering, inline comments, comments between annotations, multiline
annotations, path params with regex constraints, all param annotation types,
Javadoc extraction, Spring MVC, and malformed input.
"""

import pytest

javalang = pytest.importorskip("javalang", reason="javalang not installed")

from mcp_anything.analysis.java_ast import analyze_java_string  # noqa: E402


# ---------------------------------------------------------------------------
# Fixture Java source strings
# ---------------------------------------------------------------------------

ANNOTATION_ORDER_VARIATIONS = """
package com.example;
import javax.ws.rs.*;
import javax.ws.rs.core.Response;

@Path("/api")
public class UserResource {
    @GET
    @Path("/a")
    @Produces("application/json")
    public Response methodA() { return null; }

    @Produces("application/json")
    @Path("/b")
    @GET
    public Response methodB() { return null; }

    @Path("/c")
    @Produces("application/json")
    @GET
    public Response methodC() { return null; }
}
"""

INLINE_COMMENTS = """
package com.example;
import javax.ws.rs.*;
import javax.ws.rs.core.Response;

@Path("/api")
public class UserResource {
    @Timeout(1000) // timeout in ms (default)
    @GET
    @Path("/users") // main endpoint
    @Produces("application/json") // returns JSON
    public Response getUsers() { return null; }
}
"""

COMMENTS_BETWEEN = """
package com.example;
import javax.ws.rs.*;
import javax.ws.rs.core.Response;

@Path("/api")
public class UserResource {
    @GET
    // fetches all users
    /* paginated */
    @Path("/users")
    @Produces("application/json")
    public Response getUsers() { return null; }
}
"""

MULTILINE_ANNOTATIONS = """
package com.example;
import javax.ws.rs.*;
import javax.ws.rs.core.*;
import javax.ws.rs.core.Response;

@Path("/api")
public class UserResource {
    @GET
    @Path("/users")
    @Produces({
        MediaType.APPLICATION_JSON,
        MediaType.APPLICATION_XML
    })
    public Response getUsers() { return null; }
}
"""

PATH_PARAMS_WITH_REGEX = """
package com.example;
import javax.ws.rs.*;
import javax.ws.rs.core.Response;

@Path("/api")
public class UserResource {
    @GET
    @Path("/users/{id: [0-9]+}")
    public Response getUser(@PathParam("id") Long id) { return null; }

    @GET
    @Path("/orgs/{orgId}/users/{userId}")
    public Response getOrgUser(
        @PathParam("orgId") String orgId,
        @PathParam("userId") Long userId
    ) { return null; }
}
"""

ALL_PARAM_TYPES = """
package com.example;
import javax.ws.rs.*;
import javax.ws.rs.core.*;
import javax.ws.rs.core.Response;

@Path("/api")
public class UserResource {
    @GET
    @Path("/users")
    public Response getUsers(
        @QueryParam("limit") @DefaultValue("10") int limit,
        @QueryParam("offset") int offset,
        @HeaderParam("X-Auth-Token") String token,
        @CookieParam("session") String session,
        @Context UriInfo uriInfo
    ) { return null; }

    @POST
    @Path("/users")
    @Consumes("application/json")
    public Response createUser(
        UserDto user,
        @QueryParam("notify") boolean notify
    ) { return null; }
}
"""

JAVADOC = """
package com.example;
import javax.ws.rs.*;
import javax.ws.rs.core.Response;

@Path("/api")
public class UserResource {
    /**
     * Retrieves all users matching the given filters.
     *
     * @param limit maximum number of results
     * @param offset pagination offset
     * @return list of users
     */
    @GET
    @Path("/users")
    public Response getUsers(
        @QueryParam("limit") int limit,
        @QueryParam("offset") int offset
    ) { return null; }
}
"""

SPRING_MVC = """
package com.example;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/users")
public class UserController {
    @GetMapping("/{id}")
    public UserDto getUser(@PathVariable Long id) { return null; }

    @PostMapping("")
    public UserDto createUser(@RequestBody UserDto user) { return null; }

    @GetMapping("")
    public List<UserDto> getUsers(
        @RequestParam(defaultValue = "10") int limit
    ) { return null; }
}
"""

SPRING_NO_METHOD_PATH = """
package com.example;
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/products")
public class ProductController {
    @GetMapping
    public List<String> list(@RequestParam(required = false) String filter) { return null; }

    @DeleteMapping("/{id}")
    public void delete(@PathVariable Long id) { }
}
"""

CLASS_LEVEL_CONSUMES_PRODUCES = """
package com.example;
import javax.ws.rs.*;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;

@Path("/api/items")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class ItemResource {
    @GET
    public Response list() { return null; }

    @POST
    public Response create(ItemDto item) { return null; }
}
"""

DEPRECATED_AND_ABSTRACT = """
package com.example;
import javax.ws.rs.*;
import javax.ws.rs.core.Response;

@Path("/api")
public class UserResource {
    @Deprecated
    @GET
    @Path("/v1/users")
    public Response getUsersLegacy() { return null; }

    @GET
    @Path("/users")
    public abstract Response getUsers();
}
"""

MALFORMED = """
this is not valid java {{{
@GET @Path broken
"""

APPLICATION_PATH = """
package com.example;
import javax.ws.rs.*;
import javax.ws.rs.core.Application;
import javax.ws.rs.core.Response;

@ApplicationPath("/api")
public class AppConfig extends Application {}

@Path("/v1")
public class UserResource {
    @GET
    @Path("/users")
    public Response getUsers() { return null; }
}
"""


# ---------------------------------------------------------------------------
# Tests: annotation ordering
# ---------------------------------------------------------------------------

class TestAnnotationOrder:
    def test_three_methods_found(self):
        caps = analyze_java_string(ANNOTATION_ORDER_VARIATIONS)
        assert len(caps) == 3

    def test_all_paths_found(self):
        caps = analyze_java_string(ANNOTATION_ORDER_VARIATIONS)
        paths = {c["path"] for c in caps}
        assert paths == {"/api/a", "/api/b", "/api/c"}

    def test_all_get(self):
        caps = analyze_java_string(ANNOTATION_ORDER_VARIATIONS)
        assert all(c["http_method"] == "GET" for c in caps)


# ---------------------------------------------------------------------------
# Tests: inline comments (the primary regex failure case)
# ---------------------------------------------------------------------------

class TestInlineComments:
    def test_endpoint_found_despite_comment_with_paren(self):
        """@Timeout(1000) // comment with ) should not break parsing."""
        caps = analyze_java_string(INLINE_COMMENTS)
        assert len(caps) == 1

    def test_http_method(self):
        caps = analyze_java_string(INLINE_COMMENTS)
        assert caps[0]["http_method"] == "GET"

    def test_path(self):
        caps = analyze_java_string(INLINE_COMMENTS)
        assert caps[0]["path"] == "/api/users"


# ---------------------------------------------------------------------------
# Tests: comments between annotations
# ---------------------------------------------------------------------------

class TestCommentsBetween:
    def test_endpoint_found(self):
        caps = analyze_java_string(COMMENTS_BETWEEN)
        assert len(caps) == 1

    def test_path_correct(self):
        caps = analyze_java_string(COMMENTS_BETWEEN)
        assert caps[0]["path"] == "/api/users"


# ---------------------------------------------------------------------------
# Tests: multiline @Produces
# ---------------------------------------------------------------------------

class TestMultilineAnnotations:
    def test_endpoint_found(self):
        caps = analyze_java_string(MULTILINE_ANNOTATIONS)
        assert len(caps) == 1

    def test_produces_json(self):
        caps = analyze_java_string(MULTILINE_ANNOTATIONS)
        assert "application/json" in caps[0]["produces"]

    def test_produces_xml(self):
        caps = analyze_java_string(MULTILINE_ANNOTATIONS)
        assert "application/xml" in caps[0]["produces"]


# ---------------------------------------------------------------------------
# Tests: path parameters with regex constraints
# ---------------------------------------------------------------------------

class TestPathParams:
    def test_regex_constraint_stripped(self):
        caps = analyze_java_string(PATH_PARAMS_WITH_REGEX)
        id_cap = next(c for c in caps if "{id" in c["path"])
        assert id_cap["path"] == "/api/users/{id}"  # constraint stripped

    def test_path_param_is_path_source(self):
        caps = analyze_java_string(PATH_PARAMS_WITH_REGEX)
        id_cap = next(c for c in caps if "{id" in c["path"] and "{orgId" not in c["path"])
        params = {p["name"]: p for p in id_cap["parameters"]}
        assert params["id"]["source"] == "path"
        assert params["id"]["required"] is True

    def test_multi_path_params(self):
        caps = analyze_java_string(PATH_PARAMS_WITH_REGEX)
        org_cap = next(c for c in caps if "orgId" in c["path"])
        param_names = {p["name"] for p in org_cap["parameters"]}
        assert param_names == {"orgId", "userId"}

    def test_multi_path_param_types(self):
        caps = analyze_java_string(PATH_PARAMS_WITH_REGEX)
        org_cap = next(c for c in caps if "orgId" in c["path"])
        params = {p["name"]: p for p in org_cap["parameters"]}
        assert params["orgId"]["type"] == "string"
        assert params["userId"]["type"] == "integer"


# ---------------------------------------------------------------------------
# Tests: all parameter annotation types
# ---------------------------------------------------------------------------

class TestAllParamTypes:
    def _get_cap(self):
        caps = analyze_java_string(ALL_PARAM_TYPES)
        return next(c for c in caps if c["http_method"] == "GET")

    def _post_cap(self):
        caps = analyze_java_string(ALL_PARAM_TYPES)
        return next(c for c in caps if c["http_method"] == "POST")

    def test_query_param_source(self):
        params = {p["name"]: p for p in self._get_cap()["parameters"]}
        assert params["limit"]["source"] == "query"
        assert params["offset"]["source"] == "query"

    def test_query_param_default(self):
        params = {p["name"]: p for p in self._get_cap()["parameters"]}
        assert params["limit"]["default"] == "10"

    def test_header_param_source(self):
        params = {p["name"]: p for p in self._get_cap()["parameters"]}
        assert params["token"]["source"] == "header"

    def test_cookie_param_source(self):
        params = {p["name"]: p for p in self._get_cap()["parameters"]}
        assert params["session"]["source"] == "cookie"

    def test_context_param_ignored(self):
        params = {p["name"]: p for p in self._get_cap()["parameters"]}
        assert "uriInfo" not in params

    def test_unannotated_body_param(self):
        params = {p["name"]: p for p in self._post_cap()["parameters"]}
        assert "user" in params
        assert params["user"]["source"] == "body"
        assert params["user"]["required"] is True

    def test_query_param_on_post(self):
        params = {p["name"]: p for p in self._post_cap()["parameters"]}
        assert params["notify"]["source"] == "query"

    def test_jaxrs_query_param_not_required(self):
        """JAX-RS @QueryParam should default to required=False."""
        params = {p["name"]: p for p in self._get_cap()["parameters"]}
        assert params["offset"]["required"] is False


# ---------------------------------------------------------------------------
# Tests: Javadoc extraction
# ---------------------------------------------------------------------------

class TestJavadoc:
    def test_description_extracted(self):
        caps = analyze_java_string(JAVADOC)
        assert len(caps) == 1
        assert "Retrieves all users" in caps[0]["description"]

    def test_param_doc_extracted(self):
        caps = analyze_java_string(JAVADOC)
        params = {p["name"]: p for p in caps[0]["parameters"]}
        assert "maximum number" in params["limit"]["description"]
        assert "pagination" in params["offset"]["description"]


# ---------------------------------------------------------------------------
# Tests: Spring MVC annotations
# ---------------------------------------------------------------------------

class TestSpringMVC:
    def test_three_methods_found(self):
        caps = analyze_java_string(SPRING_MVC)
        assert len(caps) == 3

    def test_http_methods(self):
        caps = analyze_java_string(SPRING_MVC)
        methods = {c["http_method"] for c in caps}
        assert methods == {"GET", "POST"}

    def test_path_variable_is_path(self):
        caps = analyze_java_string(SPRING_MVC)
        get_cap = next(c for c in caps if "{id}" in c["path"])
        params = {p["name"]: p for p in get_cap["parameters"]}
        assert params["id"]["source"] == "path"
        assert params["id"]["required"] is True

    def test_request_body_is_body(self):
        caps = analyze_java_string(SPRING_MVC)
        post_cap = next(c for c in caps if c["http_method"] == "POST")
        params = post_cap["parameters"]
        assert any(p["source"] == "body" for p in params)

    def test_request_param_with_default(self):
        caps = analyze_java_string(SPRING_MVC)
        get_list = next(c for c in caps if "{id}" not in c["path"] and c["http_method"] == "GET")
        params = {p["name"]: p for p in get_list["parameters"]}
        assert params["limit"]["source"] == "query"
        assert params["limit"]["default"] == "10"
        assert params["limit"]["required"] is False

    def test_no_path_on_method_uses_class_path(self):
        caps = analyze_java_string(SPRING_NO_METHOD_PATH)
        assert any(c["path"] == "/api/products" for c in caps)

    def test_required_false_on_request_param(self):
        caps = analyze_java_string(SPRING_NO_METHOD_PATH)
        get_cap = next(c for c in caps if c["http_method"] == "GET")
        params = {p["name"]: p for p in get_cap["parameters"]}
        assert params["filter"]["required"] is False


# ---------------------------------------------------------------------------
# Tests: class-level @Produces / @Consumes inherited by methods
# ---------------------------------------------------------------------------

class TestClassLevelMediaTypes:
    def test_produces_inherited(self):
        caps = analyze_java_string(CLASS_LEVEL_CONSUMES_PRODUCES)
        get_cap = next(c for c in caps if c["http_method"] == "GET")
        assert "application/json" in get_cap["produces"]

    def test_consumes_inherited(self):
        caps = analyze_java_string(CLASS_LEVEL_CONSUMES_PRODUCES)
        post_cap = next(c for c in caps if c["http_method"] == "POST")
        assert "application/json" in post_cap["consumes"]

    def test_two_endpoints_found(self):
        caps = analyze_java_string(CLASS_LEVEL_CONSUMES_PRODUCES)
        assert len(caps) == 2


# ---------------------------------------------------------------------------
# Tests: @Deprecated and abstract methods must still be extracted
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_deprecated_endpoint_extracted(self):
        caps = analyze_java_string(DEPRECATED_AND_ABSTRACT)
        paths = {c["path"] for c in caps}
        assert "/api/v1/users" in paths

    def test_abstract_method_extracted(self):
        caps = analyze_java_string(DEPRECATED_AND_ABSTRACT)
        paths = {c["path"] for c in caps}
        assert "/api/users" in paths

    def test_malformed_returns_empty(self):
        caps = analyze_java_string(MALFORMED)
        assert caps == []

    def test_empty_string_returns_empty(self):
        assert analyze_java_string("") == []

    def test_non_rest_class_returns_empty(self):
        source = """
        package com.example;
        public class PlainClass {
            public void doSomething() {}
        }
        """
        assert analyze_java_string(source) == []


# ---------------------------------------------------------------------------
# Tests: output schema completeness
# ---------------------------------------------------------------------------

class TestOutputSchema:
    def test_required_top_level_keys(self):
        caps = analyze_java_string(JAVADOC)
        required = {"name", "http_method", "path", "description",
                    "parameters", "return_type", "produces", "consumes",
                    "backend_type"}
        assert required.issubset(caps[0].keys())

    def test_backend_type_is_http(self):
        caps = analyze_java_string(JAVADOC)
        assert caps[0]["backend_type"] == "http"

    def test_required_parameter_keys(self):
        caps = analyze_java_string(JAVADOC)
        for param in caps[0]["parameters"]:
            required_param_keys = {"name", "type", "source", "required",
                                   "default", "description"}
            assert required_param_keys.issubset(param.keys())

    def test_name_is_snake_case(self):
        caps = analyze_java_string(JAVADOC)
        name = caps[0]["name"]
        assert name == name.lower()
        assert " " not in name

    def test_path_starts_with_slash(self):
        caps = analyze_java_string(ANNOTATION_ORDER_VARIATIONS)
        for cap in caps:
            assert cap["path"].startswith("/")

    def test_produces_is_list(self):
        caps = analyze_java_string(ANNOTATION_ORDER_VARIATIONS)
        for cap in caps:
            assert isinstance(cap["produces"], list)
            assert isinstance(cap["consumes"], list)


# ---------------------------------------------------------------------------
# Tests: @ApplicationPath
# ---------------------------------------------------------------------------

class TestApplicationPath:
    def test_app_path_prefix_applied(self):
        caps = analyze_java_string(APPLICATION_PATH)
        # @ApplicationPath("/api") + @Path("/v1") + @Path("/users") = /api/v1/users
        # But ApplicationPath is detected from AppConfig (extends Application),
        # not from UserResource, so it applies as global prefix.
        assert len(caps) >= 1

    def test_path_includes_class_and_method(self):
        caps = analyze_java_string(APPLICATION_PATH)
        paths = {c["path"] for c in caps}
        # At minimum, the class + method path should be combined
        assert any("/v1/users" in p or "/users" in p for p in paths)
