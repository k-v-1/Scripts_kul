from coordscripts import qout2xyz
import numpy as np
import rmsd
import os


def main2():
    indir = '/home/u0133458/Documents/Calc/un2/geomtest/s0/'
    allfls = os.listdir(indir)
    allfls.sort()
    rmsdmat = np.zeros([len(allfls), len(allfls)])
    for rotat in ['kabsch']:  # , 'quaternion']: rot doesnt matter
        for reord in ['hungarian', 'distance', 'brute']:
            for i, fl1 in enumerate(['1b1s0.out']):
                for j, fl2 in enumerate(allfls):
                    file1 = indir + fl1
                    xyz1 = qout2xyz(file1, write=False)
                    xyz_at1 = np.array([k[0] for k in xyz1])
                    xyz_coord1 = np.array([k[1:4] for k in xyz1])
                    file2 = indir + fl2
                    xyz2 = qout2xyz(file2, write=False)
                    xyz_at2 = np.array([k[0] for k in xyz2])
                    xyz_coord2 = np.array([k[1:4] for k in xyz2])

                    # print(i, i + j)
                    result = rmsd_main_adapt(xyz_coord1, xyz_at1, xyz_coord2, xyz_at2,
                                             reorder_method=reord, rotation=rotat, reorder=True,
                                             outname=None)
                    rmsdmat[i, i + j] = result
                    print(result)
            print(allfls)
            # [print(list(k)) for k in rmsdmat]
            # print([rmsdmat[k, k] for k in range(len(rmsdmat))])


def main():
    indir = '/home/u0133458/Documents/Calc/un2/geomtest/s0/'
    # allfls = []
    # [allfls.append('qch1/'+i) for i in os.listdir(indir+'qch1/') if i.endswith('.out')]
    # [allfls.append('qch2/'+i) for i in os.listdir(indir+'qch2/') if i.endswith('.out')]
    allfls = os.listdir(indir)
    allfls.sort()
    rmsdmat = np.zeros([len(allfls), len(allfls)])
    # print(allfls)
    # rmsdmat = [[0]*(len(allfls)+1)]*(len(allfls)+1)
    # print(rmsdmat)
    for i, fl1 in enumerate(allfls):
        for j, fl2 in enumerate(allfls[i:]):
            file1 = indir + fl1
            xyz1 = qout2xyz(file1, write=False)
            xyz_at1 = np.array([k[0] for k in xyz1])
            xyz_coord1 = np.array([k[1:4] for k in xyz1])
            file2 = indir + fl2
            xyz2 = qout2xyz(file2, write=False)
            xyz_at2 = np.array([k[0] for k in xyz2])
            xyz_coord2 = np.array([k[1:4] for k in xyz2])

            print(i, i + j)
            # print(fl1, fl2)
            result = rmsd_main_adapt(xyz_coord1, xyz_at1, xyz_coord2, xyz_at2, reorder_method="brute")
            # print(result)
            rmsdmat[i, i + j] = result
            # rmsdmat[i][0] = fl1
            # rmsdmat[0][j] = fl2
    [print(list(k)) for k in rmsdmat]
    # print(rmsdmat)
    print(allfls)


def rmsd_main_adapt(p_all, p_all_atoms, q_all, q_all_atoms,
                    reorder=True, reorder_method="hungarian", rotation="kabsch", use_reflect=True,
                    outname=None):
    copy = rmsd.copy
    sys = rmsd.sys
    p_size = p_all.shape[0]
    q_size = q_all.shape[0]

    if not p_size == q_size:
        print("error: Structures not same size")
        sys.exit()

    if np.count_nonzero(p_all_atoms != q_all_atoms):
        msg = """
    error: Atoms are not in the same order.

    Use --reorder to align the atoms (can be expensive for large structures).

    Please see --help or documentation for more information or
    https://github.com/charnley/rmsd for further examples.
    """
        print(msg)
        sys.exit()

    # Set local view
    p_view = None
    q_view = None

    # if args.ignore_hydrogen:
    #     assert type(p_all_atoms[0]) != str
    #     assert type(q_all_atoms[0]) != str
    #     p_view = np.where(p_all_atoms != 1)
    #     q_view = np.where(q_all_atoms != 1)
    #
    # elif args.remove_idx:
    #     index = range(p_size)
    #     index = set(index) - set(args.remove_idx)
    #     index = list(index)
    #     p_view = index
    #     q_view = index
    #
    # elif args.add_idx:
    #     p_view = args.add_idx
    #     q_view = args.add_idx

    # Set local view
    if p_view is None:
        p_coord = copy.deepcopy(p_all)
        q_coord = copy.deepcopy(q_all)
        p_atoms = copy.deepcopy(p_all_atoms)
        q_atoms = copy.deepcopy(q_all_atoms)

    else:
        p_coord = copy.deepcopy(p_all[p_view])
        q_coord = copy.deepcopy(q_all[q_view])
        p_atoms = copy.deepcopy(p_all_atoms[p_view])
        q_atoms = copy.deepcopy(q_all_atoms[q_view])

    # Recenter to centroid
    p_cent = rmsd.centroid(p_coord)
    q_cent = rmsd.centroid(q_coord)
    p_coord -= p_cent
    q_coord -= q_cent

    # set rotation method
    if rotation.lower() == "kabsch":
        rotation_method = rmsd.kabsch_rmsd
    elif rotation.lower() == "quaternion":
        rotation_method = rmsd.quaternion_rmsd
    else:
        rotation_method = None

    # set reorder method
    if not reorder:
        reorder_method = None
    # elif reorder_method == "qml":
    #     reorder_method = rmsd.reorder_similarity
    elif reorder_method == "hungarian":
        reorder_method = rmsd.reorder_hungarian
    elif reorder_method == "intertia-hungarian":
        reorder_method = rmsd.reorder_inertia_hungarian
    elif reorder_method == "brute":
        reorder_method = rmsd.reorder_brute
    elif reorder_method == "distance":
        reorder_method = rmsd.reorder_distance

    # Save the resulting RMSD
    result_rmsd = None

    # if args.use_reflections:
    if use_reflect:

        result_rmsd, _, _, q_review = rmsd.check_reflections(
            p_atoms,
            q_atoms,
            p_coord,
            q_coord,
            reorder_method=reorder_method,
            rotation_method=rotation_method,
        )
    #
    # elif args.use_reflections_keep_stereo:
    #
    #     result_rmsd, _, _, q_review = check_reflections(
    #         p_atoms,
    #         q_atoms,
    #         p_coord,
    #         q_coord,
    #         reorder_method=reorder_method,
    #         rotation_method=rotation_method,
    #         keep_stereo=True,
    #     )

    # elif args.reorder:
    if reorder:
        q_review = reorder_method(p_atoms, q_atoms, p_coord, q_coord)
        q_coord = q_coord[q_review]
        # q_atoms = q_atoms[q_review]

        # if not all(p_atoms == q_atoms):
        #     print(
        #         "error: Structure not aligned. "
        #         "Please submit bug report at "
        #         "http://github.com/charnley/rmsd"
        #     )
        #     sys.exit()

    # print result
    if outname is not None:

        # if reorder:
        #     if q_review.shape[0] != q_all.shape[0]:
        #         print(
        #             "error: Reorder length error. "
        #             "Full atom list needed for --print"
        #         )
        #         quit()
        #
        #     q_all = q_all[q_review]
        #     q_all_atoms = q_all_atoms[q_review]

        # Get rotation matrix
        U = rmsd.kabsch(q_coord, p_coord)

        # recenter all atoms and rotate all atoms
        q_all -= q_cent
        q_all = np.dot(q_all, U)

        # center q on p's original coordinates
        q_all += p_cent

        # done and done
        xyz = rmsd.set_coordinates(
            q_all_atoms, q_all, title=f"{outname} - modified"
        )
        print(xyz)

    else:
        if result_rmsd:
            pass

        elif rotation_method is None:
            result_rmsd = rmsd.rmsd(p_coord, q_coord)

        else:
            result_rmsd = rotation_method(p_coord, q_coord)

        # print("{0}".format(result_rmsd))
        return float(result_rmsd)


if __name__ == '__main__':
    main2()
