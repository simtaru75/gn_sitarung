ARG BASE_IMAGE_VERSION
FROM geonode/geoserver:${BASE_IMAGE_VERSION}

# Override default init task with a robust password-sync that verifies the
# change succeeded and only writes the init lock on success (retries next boot
# otherwise). See ./tasks.py for details.
COPY tasks.py /usr/local/tomcat/tmp/tasks.py