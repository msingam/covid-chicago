import logging
import numpy as np
import pandas as pd
import os
import matplotlib as mpl
from datetime import date, timedelta
import shutil

from dotenv import load_dotenv

from load_paths import load_box_paths
from processing_helpers import *
from simulation_helpers import *
from simulation_setup import *

log = logging.getLogger(__name__)

mpl.rcParams['pdf.fonttype'] = 42
Location = 'Local'  # 'NUCLUSTER'

today = date.today()


# parameter samples
def generateParameterSamples(samples, pop, first_day):
        df =  pd.DataFrame()
        df['sample_num'] = range(samples)
        df['speciesS'] = pop
        df['initialAs'] = 10 #np.random.uniform(1, 5, samples)

        df['incubation_pd'] = np.random.uniform(4.2, 6.63, samples)
        df['time_to_symptoms'] = np.random.uniform(1, 5, samples)
        df['time_to_hospitalization'] = np.random.uniform(2, 10, samples)
        df['time_to_critical'] = np.random.uniform(4, 9, samples)
        df['time_to_death'] = np.random.uniform(3, 11, samples)
        df['recovery_rate_asymp'] = np.random.uniform(6, 16, samples)
        df['recovery_rate_mild'] = np.random.uniform(19.4, 21.3, samples)
        df['recovery_rate_hosp'] = np.random.uniform(19.5, 21.1, samples)
        df['recovery_rate_crit'] = np.random.uniform(25.3, 31.6, samples)
        df['fraction_symptomatic'] = np.random.uniform(0.5, 0.8, samples)
        df['fraction_severe'] = np.random.uniform(0.2, 0.5, samples)
        df['fraction_critical'] = np.random.uniform(0.2, 0.5, samples)
        #df['fraction_critical'] = np.random.uniform(0.15, 0.35, samples)
        #df['fraction_critical'] = np.random.uniform(0.15, 0.45, samples)
        #df['cfr'] = np.random.uniform(0.008, 0.022, samples)
        #df['cfr'] = np.random.uniform(0.0009, 0.0017, samples)
        #df['cfr'] = np.random.uniform(0.00445, 0.01185, samples)
        df['cfr'] = np.random.uniform(0.002675, 0.007775, samples)
        df['fraction_dead'] = df.apply(lambda x: x['cfr'] / x['fraction_severe'], axis=1)
        df['fraction_hospitalized'] = df.apply(lambda x: 1 - x['fraction_critical'] - x['fraction_dead'], axis=1)
        df['reduced_inf_of_det_cases'] = np.random.uniform(0.5, 0.9, samples)
        df['d_Sym'] = np.random.uniform(0.2, 0.3, samples)
        df['d_Sys'] = np.random.uniform(0.7, 0.9, samples)
        df['d_As'] = np.random.uniform(0, 0, samples)
        #df['Ki'] = np.random.uniform(2.e-7, 2.5e-7, samples)

        df['social_multiplier_1'] = np.random.uniform(0.9, 1, samples)
        df['social_multiplier_2'] = np.random.uniform(0.6, 0.9, samples)
        df['social_multiplier_3'] = np.random.uniform( 0.05 , 0.3, samples) #0.2, 0.6

        df['socialDistance_time1'] = DateToTimestep(date(2020, 3, 12), startdate=first_day)
        df['socialDistance_time2'] = DateToTimestep(date(2020, 3, 17), startdate=first_day)
        df['socialDistance_time3'] = DateToTimestep(date(2020, 3, 21), startdate=first_day)

        df.to_csv(os.path.join(temp_exp_dir, "sampled_parameters.csv"), index=False)
        return(df)

def replaceParameters(df, Ki_i,  sample_nr, emodlname,  scen_num) :
    fin = open(os.path.join(temp_exp_dir,emodlname), "rt")
    data = fin.read()
    data = data.replace('@speciesS@', str(df.speciesS[sample_nr]))
    data = data.replace('@initialAs@', str(df.initialAs[sample_nr]))
    data = data.replace('@incubation_pd@', str(df.incubation_pd[sample_nr]))
    data = data.replace('@time_to_symptoms@', str(df.time_to_symptoms[sample_nr]))
    data = data.replace('@time_to_hospitalization@', str(df.time_to_hospitalization[sample_nr]))
    data = data.replace('@time_to_critical@', str(df.time_to_critical[sample_nr]))
    data = data.replace('@time_to_death@', str(df.time_to_death[sample_nr]))
    data = data.replace('@fraction_hospitalized@', str(df.fraction_hospitalized[sample_nr]))
    data = data.replace('@fraction_symptomatic@', str(df.fraction_symptomatic[sample_nr]))
    data = data.replace('@fraction_severe@', str(df.fraction_severe[sample_nr]))
    data = data.replace('@fraction_critical@', str(df.fraction_critical[sample_nr]))
    data = data.replace('@reduced_inf_of_det_cases@', str(df.reduced_inf_of_det_cases[sample_nr]))
    data = data.replace('@fraction_dead@', str(df.fraction_dead[sample_nr]))
    data = data.replace('@d_As@', str(df.d_As[sample_nr]))
    data = data.replace('@d_Sym@', str(df.d_Sym[sample_nr]))
    data = data.replace('@d_Sys@', str(df.d_Sys[sample_nr]))
    data = data.replace('@recovery_rate_asymp@', str(df.recovery_rate_asymp[sample_nr]))
    data = data.replace('@recovery_rate_mild@', str(df.recovery_rate_mild[sample_nr]))
    data = data.replace('@recovery_rate_hosp@', str(df.recovery_rate_hosp[sample_nr]))
    data = data.replace('@recovery_rate_crit@', str(df.recovery_rate_crit[sample_nr]))
    data = data.replace('@Ki@', '%.09f'% Ki_i)
    data = data.replace('@social_multiplier_1@',  str(df.social_multiplier_1[sample_nr]))
    data = data.replace('@social_multiplier_2@',  str(df.social_multiplier_2[sample_nr]))
    data = data.replace('@social_multiplier_3@',  str(df.social_multiplier_3[sample_nr]))
    data = data.replace('@socialDistance_time1@',  str(df.socialDistance_time1[sample_nr]))
    data = data.replace('@socialDistance_time2@',  str(df.socialDistance_time2[sample_nr]))
    data = data.replace('@socialDistance_time3@',  str(df.socialDistance_time3[sample_nr]))

    fin.close()
    fin = open(os.path.join(temp_dir, "simulation_"+str(scen_num)+".emodl"), "wt")
    fin.write(data)
    fin.close()


def generateScenarios(simulation_population, Kivalues, duration, monitoring_samples,
                      nruns, sub_samples, modelname, first_day, Location):
    lst = []
    scen_num = 0
    dfparam = generateParameterSamples(samples=sub_samples, pop=simulation_population, first_day=first_day)
    for sample in range(sub_samples):
        for i in Kivalues:
            scen_num += 1
            #print(i)

            #lst.append([simulation_population, sample, nruns, scen_num, i, Kval])
            lst.append([sample, scen_num, i , first_day, simulation_population])
            replaceParameters(df=dfparam, Ki_i=i, sample_nr= sample, emodlname=modelname, scen_num=scen_num)

            # adjust model.cfg
            fin = open(os.path.join(temp_exp_dir,"model.cfg"), "rt")
            data_cfg = fin.read()
            data_cfg = data_cfg.replace('@duration@', str(duration))
            data_cfg = data_cfg.replace('@monitoring_samples@', str(monitoring_samples))
            data_cfg = data_cfg.replace('@nruns@', str(nruns))
            if not Location == 'Local':
                data_cfg = data_cfg.replace('trajectories', 'trajectories_scen' + str(scen_num))
            elif sys.platform not in ["win32", "cygwin"]:
                # When running on Linux or OSX (and not in Quest), assume the
                # trajectories directory is in the working directory.
                traj_fname = os.path.join('trajectories',
                                          'trajectories_scen' + str(scen_num))
                data_cfg = data_cfg.replace('trajectories', traj_fname)
            elif Location == 'Local' :
                data_cfg = data_cfg.replace('trajectories', './_temp/'+exp_name+'/trajectories/trajectories_scen' + str(scen_num))
            else:
                raise RuntimeError("Unable to decide where to put the trajectories file.")
            fin.close()
            fin = open(os.path.join(temp_dir,"model_"+str(scen_num)+".cfg"), "wt")
            fin.write(data_cfg)
            fin.close()

    df = pd.DataFrame(lst, columns=['sample_num', 'scen_num', 'Ki', 'first_day', 'simulation_population'])
    df.to_csv(os.path.join(temp_exp_dir,"scenarios.csv"), index=False)
    return scen_num


if __name__ == '__main__' :
    logging.basicConfig(level="DEBUG")
    logging.getLogger("matplotlib").setLevel("INFO")  # Matplotlib has noisy debugs

    # Load parameters
    load_dotenv()

    _, _, wdir, exe_dir, git_dir = load_box_paths()
    Location = os.getenv("LOCATION") or Location

    # Only needed on non-Windows, non-Quest platforms
    docker_image = os.getenv("DOCKER_IMAGE")

    emodl_dir = os.path.join(git_dir, 'emodl')
    cfg_dir = os.path.join(git_dir, 'cfg')

    log.debug(f"Running in Location = {Location}")
    if sys.platform not in ['win32', 'cygwin']:
        log.debug(f"Running in a non-Windows environment; "
                  f'docker_image="{docker_image}"')
    log.debug(f"Working directory: wdir={wdir}")
    log.debug(f"git_dir={git_dir}")

    master_channel_list = ['susceptible', 'exposed', 'asymptomatic', 'symptomatic_mild',
                           'hospitalized', 'detected', 'critical', 'deaths', 'recovered']
    detection_channel_list = ['detected', 'detected_cumul', 'asymp_det_cumul', 'hosp_det_cumul']
    custom_channel_list = ['detected_cumul', 'symp_severe_cumul', 'asymp_det_cumul', 'hosp_det_cumul',
                           'symp_mild_cumul', 'asymp_cumul', 'hosp_cumul', 'crit_cumul']

    #============================================================
    # Experiment design, fitting parameter and population
    #=============================================================

    ### Define setting
    region = 'NMH_catchment'  # NMH_catchment  # IL  #EMS_3  # Chicago
    exp_name = today.strftime("%Y%m%d") + '_%s_updatedStartDate' % region + '_rn' + str(int(np.random.uniform(10, 99)))

    # Selected SEIR model
    emodlname = 'extendedmodel_cobey.emodl'

    # Generate folders and copy required files
    temp_dir, temp_exp_dir, trajectories_dir, sim_output_path, plot_path = makeExperimentFolder(
        exp_name,emodl_dir,emodlname, cfg_dir, wdir=wdir, git_dir=git_dir) ## GE 04/10/20 added exp_name,emodl_dir,emodlname, cfg_dir here to fix exp_name not defined error
    log.debug(f"temp_dir = {temp_dir}\n"
              f"temp_exp_dir = {temp_exp_dir}\n"
              f"trajectories_dir = {trajectories_dir}\n"
              f"sim_output_path = {sim_output_path}\n"
              f"plot_path = {plot_path}")

    ## function in simulation_setup.py
    populations, Kis, startdate = load_setting_parameter()
    #writeTxt(txtdir=temp_exp_dir, filename='setting_parameter.txt', textstring='populations =' + populations + '\nKis = ' + Kis + '\n startdate = ' + startdate)

    simulation_population = populations[region]
    number_of_samples = 2
    number_of_runs = 1
    duration = 365
    monitoring_samples = 365  # needs to be smaller than duration

    # Parameter values
    Kivalues = Kis[region]
    first_day = startdate[region]

    nscen = generateScenarios(simulation_population,
                              Kivalues,
                              nruns=number_of_runs,
                              sub_samples=number_of_samples,
                              duration = duration,
                              monitoring_samples = monitoring_samples,
                              modelname=emodlname,
                              first_day = first_day,
                              Location=Location,
                              )

    generateSubmissionFile(
        nscen, exp_name, trajectories_dir, temp_dir, temp_exp_dir,
        exe_dir=exe_dir, docker_image=docker_image)

    if Location == 'Local' :
        runExp(trajectories_dir=trajectories_dir, Location='Local')

        # Once the simulations are done
        #number_of_samples*len(Kivalues) == nscen ### to check
        combineTrajectories(Nscenarios=nscen, trajectories_dir=trajectories_dir,
                            temp_exp_dir=temp_exp_dir, deleteFiles=False)
        cleanup(temp_exp_dir=temp_exp_dir, sim_output_path=sim_output_path,
                plot_path=plot_path, delete_temp_dir=False)
        df = pd.read_csv(os.path.join(sim_output_path, 'trajectoriesDat.csv'))


        sampleplot(df, allchannels=master_channel_list, first_day=first_day,
                   plot_fname=os.path.join(plot_path, 'main_channels.png'))
        sampleplot(df, allchannels=detection_channel_list, first_day=first_day,
                   plot_fname=os.path.join('detection_channels.png'))
        sampleplot(df, allchannels=custom_channel_list, first_day=first_day,
                   plot_fname=os.path.join('cumulative_channels.png'))