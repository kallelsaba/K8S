require "yaml"

root     = File.dirname(File.expand_path(__FILE__))
cfg      = YAML.load_file("#{root}/ansible/group_vars/all/main.yml")
nodes    = cfg["nodes"]
network  = cfg["network"]
software = cfg["software"]

# ── Clé SSH Ansible ───────────────────────────────────────────────────────────
# Générée une seule fois au premier vagrant up, stockée dans .vagrant/
# vm-service s'en sert pour piloter control-plane et worker-1 sans mot de passe
SSH_KEY_PATH = "#{root}/.vagrant/ansible_key"
unless File.exist?("#{SSH_KEY_PATH}.pub")
  Dir.mkdir("#{root}/.vagrant") unless Dir.exist?("#{root}/.vagrant")
  system("ssh-keygen -t ed25519 -C ansible@vm-service -f #{SSH_KEY_PATH} -N \"\" -q")
  puts "==> Clé SSH Ansible générée dans .vagrant/ansible_key"
end
ANSIBLE_PUB_KEY  = File.read("#{SSH_KEY_PATH}.pub").strip
ANSIBLE_PRIV_KEY = File.read(SSH_KEY_PATH)

Vagrant.configure("2") do |config|
  config.vm.box              = software["box"]
  config.vm.box_check_update = false
  config.vm.boot_timeout     = 1200

  # ============================================================
  # VM 1 : vm-service  (192.168.56.10)
  # Rôle : Ansible controller, Gitea, Nexus, NFS Server
  # ============================================================
  config.vm.define "vm-service" do |svc|
    svc.vm.hostname = "vm-service"
    svc.vm.network "private_network", ip: network["service_ip"]

    svc.vm.provider "virtualbox" do |vb|
      vb.name   = "vm-service"
      vb.cpus   = nodes["service"]["cpu"]
      vb.memory = nodes["service"]["memory"]
      vb.customize ["modifyvm", :id, "--vram",        "25"]
      vb.customize ["modifyvm", :id, "--nicpromisc2", "allow-all"]
    end

    # Étape 1 : installer la clé privée Ansible dans vm-service
    svc.vm.provision "shell", name: "install-ansible-key", inline: <<-SHELL
      set -e
      install -d -m 0700 -o vagrant -g vagrant /home/vagrant/.ssh
      cat > /home/vagrant/.ssh/ansible_key <<'EOF'
#{ANSIBLE_PRIV_KEY}
EOF
      chown vagrant:vagrant /home/vagrant/.ssh/ansible_key
      chmod 600 /home/vagrant/.ssh/ansible_key
      grep -qF "#{ANSIBLE_PUB_KEY}" /home/vagrant/.ssh/authorized_keys 2>/dev/null \
        || echo "#{ANSIBLE_PUB_KEY}" >> /home/vagrant/.ssh/authorized_keys
      chmod 600 /home/vagrant/.ssh/authorized_keys
      chown vagrant:vagrant /home/vagrant/.ssh/authorized_keys
      echo "==> Clé Ansible installée dans vm-service"
    SHELL

    # Étape 2 : installer Ansible
    svc.vm.provision "shell", name: "install-ansible", inline: <<-SHELL
      set -e
      export DEBIAN_FRONTEND=noninteractive
      apt-get remove -y -qq needrestart 2>/dev/null || true
      rm -f /etc/apt/sources.list.d/ansible-ubuntu-ansible-jammy.list \
            /etc/apt/sources.list.d/ansible-ubuntu-ansible-jammy.list.save \
            /etc/apt/trusted.gpg.d/ansible-ubuntu-ansible.gpg
      apt-get update -qq
      apt-get install -y -qq software-properties-common
      add-apt-repository --yes universe || true
      apt-get install -y -qq ansible
      echo "==> $(ansible --version | head -1) prêt"
    SHELL


    # Étape 3 : provisionner vm-service elle-même (Gitea, Nexus, NFS)
    svc.vm.provision "ansible_local" do |a|
      a.playbook       = "ansible/site.yml"
      a.inventory_path = "ansible/inventory.ini"
      a.limit          = "service"
      a.tags           = "service"
      a.install        = false   # déjà installé ci-dessus
    end
  end

  # ============================================================
  # VM 2 : control-plane  (192.168.56.11)
  # Rôle : K8s master, Jenkins (pod)
  # ============================================================
  config.vm.define "control-plane" do |cp|
    cp.vm.hostname = "control-plane"
    cp.vm.network "private_network", ip: network["control_ip"]

    cp.vm.provider "virtualbox" do |vb|
      vb.name   = "control-plane"
      vb.cpus   = nodes["control"]["cpu"]
      vb.memory = nodes["control"]["memory"]
      vb.customize ["modifyvm", :id, "--vram",        "25"]
      vb.customize ["modifyvm", :id, "--nicpromisc2", "allow-all"]
    end

    # Pré-requis minimal : python3 + clé publique Ansible
    cp.vm.provision "shell", name: "bootstrap", inline: <<-SHELL
      export DEBIAN_FRONTEND=noninteractive
      apt-get remove -y -qq needrestart 2>/dev/null || true
      apt-get update -qq && apt-get install -y -qq python3 > /dev/null
      grep -qF "#{ANSIBLE_PUB_KEY}" /home/vagrant/.ssh/authorized_keys 2>/dev/null \
        || echo "#{ANSIBLE_PUB_KEY}" >> /home/vagrant/.ssh/authorized_keys
      chmod 600 /home/vagrant/.ssh/authorized_keys
      chown vagrant:vagrant /home/vagrant/.ssh/authorized_keys
      echo "==> control-plane bootstrap OK"
    SHELL
  end

  # ============================================================
  # VM 3 : worker-1  (192.168.56.12)
  # Rôle : K8s worker, pods applicatifs
  #
  # C'est la DERNIÈRE VM — son démarrage déclenche automatiquement
  # le provisioning K8s complet depuis vm-service
  # ============================================================
  config.vm.define "worker-1" do |w1|
    w1.vm.hostname = "worker-1"
    w1.vm.network "private_network", ip: network["worker1_ip"]

    w1.vm.provider "virtualbox" do |vb|
      vb.name   = "worker-1"
      vb.cpus   = nodes["worker"]["cpu"]
      vb.memory = nodes["worker"]["memory"]
      vb.customize ["modifyvm", :id, "--vram",        "25"]
      vb.customize ["modifyvm", :id, "--nicpromisc2", "allow-all"]
    end

    # Pré-requis minimal : python3 + clé publique Ansible
    w1.vm.provision "shell", name: "bootstrap", inline: <<-SHELL
      export DEBIAN_FRONTEND=noninteractive
      apt-get remove -y -qq needrestart 2>/dev/null || true
      apt-get update -qq && apt-get install -y -qq python3 > /dev/null
      grep -qF "#{ANSIBLE_PUB_KEY}" /home/vagrant/.ssh/authorized_keys 2>/dev/null \
        || echo "#{ANSIBLE_PUB_KEY}" >> /home/vagrant/.ssh/authorized_keys
      chmod 600 /home/vagrant/.ssh/authorized_keys
      chown vagrant:vagrant /home/vagrant/.ssh/authorized_keys
      echo "==> worker-1 bootstrap OK"
    SHELL

    # ── Trigger : toutes les VMs sont up → lancer le playbook K8s ──
    # Exécuté depuis vm-service via vagrant ssh
    # --skip-tags service : vm-service est déjà provisionnée
    w1.trigger.after :up do |trigger|
      trigger.info = "Toutes les VMs sont up — lancement du provisioning K8s depuis vm-service..."
      trigger.run = {
        inline: "vagrant ssh vm-service -c " \
                "\"cd /vagrant && ANSIBLE_HOST_KEY_CHECKING=False " \
                "ansible-playbook -i ansible/inventory.ini ansible/site.yml " \
                "--skip-tags service\""
      }
    end
  end

end
