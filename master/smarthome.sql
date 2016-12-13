-- phpMyAdmin SQL Dump
-- version 4.5.4
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Dec 13, 2016 at 03:20 PM
-- Server version: 5.5.53-0ubuntu0.14.04.1
-- PHP Version: 5.5.9-1ubuntu4.20

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `smarthome`
--

-- --------------------------------------------------------

--
-- Table structure for table `heating_except`
--

CREATE TABLE `heating_except` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `temp` int(11) NOT NULL,
  `date_start` datetime NOT NULL,
  `date_end` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `heating_regular`
--

CREATE TABLE `heating_regular` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `dow` int(11) NOT NULL,
  `temp` float NOT NULL,
  `time` time NOT NULL,
  `enabled` tinyint(1) NOT NULL DEFAULT '1'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `heating_regular`
--

INSERT INTO `heating_regular` (`id`, `name`, `dow`, `temp`, `time`, `enabled`) VALUES
(2, 'Dilluns feina 18', 1, 18, '06:30:00', 1),
(4, 'Dilluns nit 19', 1, 19, '22:00:00', 1),
(13, 'Dilluns tarda 20', 1, 20, '16:30:00', 1),
(14, 'Dimarts feina 18', 2, 18, '06:30:00', 1),
(15, 'Dimarts tarda 20', 2, 20, '16:30:00', 1),
(16, 'Dimarts nit 19', 2, 19, '22:00:00', 1),
(17, 'Dimecres nit 19\r\n', 3, 19, '22:00:00', 1),
(18, 'Dimecres feina 18', 3, 18, '06:30:00', 1),
(19, 'Dimecres tarda 20', 3, 20, '16:30:00', 1),
(20, 'Dijous nit 19', 4, 20, '22:00:00', 1),
(21, 'Dijous feina 18', 4, 18, '06:00:00', 1),
(22, 'Dijous tarda 20', 4, 20, '16:30:00', 1),
(23, 'Divendres nit 19', 5, 19, '23:00:00', 1),
(24, 'Divendres feina 18', 5, 18, '06:30:00', 1),
(25, 'Divendres tarda 20', 5, 20, '16:30:00', 1),
(26, 'Dissabte dia 20', 6, 20, '07:00:00', 1),
(27, 'Dissabte nit 19', 6, 19, '23:00:00', 1),
(28, 'Diumenge dia 20', 7, 20, '07:00:00', 1),
(29, 'Diumenge nit 19', 7, 19, '22:00:00', 1);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `heating_except`
--
ALTER TABLE `heating_except`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `heating_regular`
--
ALTER TABLE `heating_regular`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `heating_except`
--
ALTER TABLE `heating_except`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `heating_regular`
--
ALTER TABLE `heating_regular`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=30;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
