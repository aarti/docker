:title: Rackspace Cloud Installation
:description: Installing Docker on Ubuntu proviced by Rackspace
:keywords: Rackspace Cloud, installation, docker, linux, ubuntu

===============
Rackspace Cloud
===============

.. include:: install_unofficial.inc

Installing Docker on Ubuntu provided by Rackspace is pretty
straightforward, and you should mostly be able to follow the
:ref:`ubuntu_linux` installation guide.

**However, there is one caveat:**

If you are using any linux not already shipping with the 3.8 kernel
you will need to install it. And this is a little more difficult on
Rackspace.

Rackspace boots their servers using grub's ``menu.lst`` and does not
like non 'virtual' packages (e.g. xen compatible) kernels there,
although they do work. This makes ``update-grub`` to not have the
expected result, and you need to set the kernel manually.

**Do not attempt this on a production machine!**

.. code-block:: bash

    # update apt
    apt-get update

    # install the new kernel
    apt-get install linux-generic-lts-raring


Great, now you have kernel installed in ``/boot/``, next is to make it
boot next time.

.. code-block:: bash

    # find the exact names
    find /boot/ -name '*3.8*'

    # this should return some results


Now you need to manually edit ``/boot/grub/menu.lst``, you will find a
section at the bottom with the existing options.  Copy the top one and
substitute the new kernel into that. Make sure the new kernel is on
top, and double check kernel and initrd point to the right files.

Make special care to double check the kernel and initrd entries.

.. code-block:: bash

    # now edit /boot/grub/menu.lst
    vi /boot/grub/menu.lst

It will probably look something like this:

::

     ## ## End Default Options ##

     title		Ubuntu 12.04.2 LTS, kernel 3.8.x generic
     root		(hd0)
     kernel		/boot/vmlinuz-3.8.0-19-generic root=/dev/xvda1 ro quiet splash console=hvc0
     initrd		/boot/initrd.img-3.8.0-19-generic

     title		Ubuntu 12.04.2 LTS, kernel 3.2.0-38-virtual
     root		(hd0)
     kernel		/boot/vmlinuz-3.2.0-38-virtual root=/dev/xvda1 ro quiet splash console=hvc0
     initrd		/boot/initrd.img-3.2.0-38-virtual

     title		Ubuntu 12.04.2 LTS, kernel 3.2.0-38-virtual (recovery mode)
     root		(hd0)
     kernel		/boot/vmlinuz-3.2.0-38-virtual root=/dev/xvda1 ro quiet splash  single
     initrd		/boot/initrd.img-3.2.0-38-virtual


Reboot server (either via command line or console)

.. code-block:: bash

   # reboot

Verify the kernel was updated

.. code-block:: bash

    uname -a
    # Linux docker-12-04 3.8.0-19-generic #30~precise1-Ubuntu SMP Wed May 1 22:26:36 UTC 2013 x86_64 x86_64 x86_64 GNU/Linux

    # nice! 3.8.


Now you can finish with the :ref:`ubuntu_linux` instructions.
