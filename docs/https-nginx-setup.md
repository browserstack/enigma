## HTTPS Nginx Setup

Following are the steps to Setup Nginx in enigma

1. **Pre-requisistes** 
    - Should have a host(domain) with ssl certificats that can be attached to nginx.
    - Make sure the host points the public IP of the machine in which enigma is running on. (i.e., create an dns A record with host pointing to public IP of machine)
2. Create a folder in the root folder of enigma-public-central named `certs` which contains ssl certificate and key.
3. Copy `nginx.conf.sample` file to `nginx.conf`
3. Configure `nginx.conf` file.
    - update the hostname in the `nginx.conf` file
      ```diff
      server {
        listen 80;
      -   server_name www.yourdomain.com;
      +   server_name enigma.com;
        return 301 https://$host$request_uri;
      }
      ```

      ```diff
      server {
        listen 443 ssl;
      -   server_name www.yourdomain.com;
      +   server_name enigma.com;
      ```
      The above mentioned changes are just examples to show what needs to be changed, please add your own domain names in mentioned places.
    - update ssl certificate paths in `nginx.conf` file
      ```diff
      server {
        listen 443 ssl;
        server_name www.yourdomain.com;
        server_tokens off;

      -  ssl_certificate       /certs/<ssl_crt_file_name>;
      +  ssl_certificate       /certs/enigma.crt;
      -  ssl_certificate_key   /certs/<ssl_key_file_name>;
      +  ssl_certificate_key   /certs/enigma.key;
      ```
      The above mentioned changes are just examples to show what needs to be changed, Please add your own certificate and key file names.

4. Run the following command with your terminal in enigma-public-central root folder.
    ```
    docker run --name enigma-nginx -v <absolute_path to nginx.conf file>:/etc/nginx/nginx.conf:ro \
    -v <absolute_path to certs folder>:/certs -p 80:80 -p 443:443 -d --add-host host.docker.internal:host-gateway nginx:latest
    ```
    Make sure to update the absolute paths to the files/folders mentioned.

:tada: Congrats you are done. You should now be able to access enigma from your host.
