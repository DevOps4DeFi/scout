# Badger Scout - Opensource

This is an opensource version of the monitoring tool used by Badger Finance to watch simple ops metrics on our Etherium smart contracts.  Over time communtiy dashboards will be added.

Badger scout inspects each block on the chain and creates badger relevant events and uses Prometheus/Grafana to stored/display/work on them.

It includes a base set of UI unchangable dashboards configured by JSON that are used for alerting, and uses configuration as code wherever possible.  Additional dashboards unchangeable dashboards can be added by the community by making a pull request to add the json file into the `grafana/dashboards` directory structure.  

Terraform code is in the root directory because it required to pull modules. Maybe needs to be split into a different repo.  

All source code can be found in the `docker/ directory`. The Badger-written python collector can be found in `docker/scout`

## Development environment

The simplest way to get this up and running is to run the below commands from this directory:

```bash
cd docker
export ETHNODEURL=https://ethnode.infra.example
export 
docker-compose build
docker-compose up
```

* NOTE: once running you can access: grafana @ localhost:3000, prometheus @ localhost:9090, scout prometheus target @ localhost 8801
* Look in the docker-compose.yaml for some environment variables you can alter to change basic behavior

## Production Eivnronment

Look in the terraform directory to figure out how to build this out in the cloud.  The module is meant to work with network and loadbalancer resources provided by the DevOps4DeFi terraform-baseline module: <https://github.com/DevOps4DeFi/terraform-baseline>
More documentation is still required.

You can use the `docker/build.sh` script to build the containers and push them to the ecr repos created by terraform.

## Working with pre-made dashboards

Look in the `grafana/provisioning/datasources` directory to see the datasource that is used to access prometheus.  Note that it depends on an environment variable called: `PROMETHEUS_URL`
You can find the dashboard structure in the `grafana/dashboards` directory.  The same directory structure will be shown in Grafana.

To make changes to these dashboards add/edit/remove the JSON files in this directory and redeploy the grafana `docker-compose restart`

You can also copy the dashboards in the console and edit them, you can always export the full JSON from a dashboard built in the console and copy the JSON from the UI to paste here and change/templatize.

Note that Grafana interpolates ${VAR} of as with VAR environment variable in the yaml files in `grafana/provisioning`.
