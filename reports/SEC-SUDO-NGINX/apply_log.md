# This file is managed by Feature Factory agent-ops.
# It grants specific sudo privileges for nginx operations to the ff-ops group.

# Secure Defaults
Defaults        env_reset
Defaults        use_pty
Defaults        log_output
Defaults        secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin"
Defaults        iolog_dir="/var/log/sudo-io" # Default sudo I/O log directory

# Command Alias for Nginx binary operations
Cmnd_Alias FF_NGINX = /usr/sbin/nginx reload, /usr/sbin/nginx -t, /usr/sbin/nginx status

# Command Alias for Nginx service management via script
Cmnd_Alias FF_NGINX_RESTART_SCRIPT = /usr/local/bin/ff-nginx-restart.sh

# Allow ff-ops group to run FF_NGINX commands without password
%ff-ops ALL=(ALL) NOPASSWD: FF_NGINX, FF_NGINX_RESTART_SCRIPT