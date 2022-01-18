# Extending Volley

Volley can be extended by developing additional connectors, serializers, and model handlers. Each of these have base classes that can be inherited into your own implementations, then registered in the Engine() configuration to be used with your application.

Briefly:

- __Connectors__ handle consuming and producing data to/from a data store
- __Serializers__ convert bytes to a primitive python object
- __Model handlers__ convert primitive python object to user defined data models

Each of these can be extended with custom and community contributed plugins.